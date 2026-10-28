# Angie HTTP/3 Edge Proxy Configuration

This directory contains the Angie edge proxy configuration for HTTP/3 termination and upstream proxying to the TTV Pipeline API server.

## Overview

The Angie configuration provides:

- **HTTP/3 Edge Termination**: Handles HTTP/3 over QUIC from clients
- **HTTP/3 Upstream Proxy**: Forwards requests to Hypercorn via HTTP/3
- **TLS Certificate Management**: SSL/TLS configuration with OCSP stapling
- **QUIC Parameter Tuning**: Optimized QUIC settings for video workloads
- **Security Headers**: Comprehensive security header configuration
- **Rate Limiting**: API rate limiting with burst handling
- **Health Check Routing**: Optimized health check endpoints

## Architecture

```
Client (HTTP/3) → Angie Edge Proxy (HTTP/3) → Hypercorn ASGI (HTTP/3) → FastAPI
```

### Key Features

1. **HTTP/3 End-to-End**: Full HTTP/3 pipeline from client to application
2. **Protocol Fallbacks**: Automatic fallback to HTTP/2 and HTTP/1.1
3. **Connection Migration**: QUIC connection migration support
4. **Load Balancing**: Primary/backup upstream configuration
5. **Security**: Rate limiting, CORS, and security headers

## Configuration Files

### `angie.conf`

Main Angie configuration with:

- **HTTP/3 Listeners**: TCP and UDP listeners for HTTP/3
- **Upstream Configuration**: HTTP/3 upstream with fallback
- **SSL/TLS Settings**: Enhanced TLS 1.3 configuration
- **QUIC Parameters**: Tuned for optimal performance
- **Security Headers**: Comprehensive security configuration
- **Rate Limiting**: API protection with burst handling

### Key Configuration Sections

#### HTTP/3 Listeners
```nginx
listen 443 ssl http2;
listen 443 quic;
```

#### Upstream Configuration
```nginx
upstream api_backend {
    server api:8443 quic=on max_fails=3 fail_timeout=30s;
    server api:8000 backup max_fails=3 fail_timeout=30s;
    keepalive 32;
}
```

#### QUIC Parameters
```nginx
quic_max_concurrent_streams 128;
quic_active_connection_id_limit 8;
quic_max_ack_delay 25ms;
quic_max_udp_payload_size 1472;
```

#### HTTP/3 Upstream Proxy
```nginx
proxy_pass http://api_backend;
proxy_http_version 3.0;
proxy_http2_push_preload on;
```

## Setup and Deployment

### 1. Generate Certificates

```bash
# Generate development certificates
./scripts/setup_http3_certs.sh

# For production, place certificates in certs/ directory:
# - certs/cert.pem (SSL certificate)
# - certs/key.pem (Private key)
# - certs/quic_host.key (QUIC host key)
```

### 2. Validate Configuration

```bash
# Full validation
./scripts/validate_angie_config.sh

# Syntax only
./scripts/validate_angie_config.sh --syntax-only

# Generate report
./scripts/validate_angie_config.sh --report
```

### 3. Deploy with Docker Compose

```bash
# Start services
docker-compose -f docker-compose.http3.yml up -d

# Check logs
docker-compose -f docker-compose.http3.yml logs -f angie
```

## Testing

### Configuration Tests

```bash
# Run configuration tests
python -m pytest tests/test_angie_http3.py::TestAngieHTTP3Config -v

# Run integration tests (requires running services)
python -m pytest tests/test_angie_http3.py::TestAngieHTTP3Connectivity -v -m integration
```

### Manual Testing

```bash
# Test HTTP/3 connectivity
curl --http3 https://localhost/healthz

# Test protocol negotiation
curl -v https://localhost/healthz | grep -i alt-svc

# Test rate limiting
for i in {1..30}; do curl -s -o /dev/null -w "%{http_code}\n" https://localhost/healthz; done
```

## Performance Tuning

### QUIC Parameters

The configuration includes optimized QUIC parameters:

- **Max Concurrent Streams**: 128 (balanced for API workloads)
- **Connection ID Limit**: 8 (supports connection migration)
- **Max ACK Delay**: 25ms (low latency)
- **UDP Payload Size**: 1472 bytes (optimal for most networks)

### Connection Management

- **Keepalive**: 32 connections to upstream
- **Keepalive Timeout**: 60 seconds
- **Max Requests**: 1000 per connection

### Rate Limiting

- **API Zone**: 10 requests/second per IP
- **Burst Zone**: 50 requests/second per IP
- **Burst Allowance**: 20 requests (API), 100 requests (burst)

## Security Configuration

### TLS/SSL

- **Protocols**: TLS 1.2, TLS 1.3 (prefer TLS 1.3)
- **Ciphers**: Modern cipher suites with ChaCha20-Poly1305
- **Session Cache**: 10MB shared cache
- **OCSP Stapling**: Enabled for certificate validation

### Security Headers

- **X-Frame-Options**: DENY
- **X-Content-Type-Options**: nosniff
- **X-XSS-Protection**: Enabled with blocking
- **Referrer-Policy**: strict-origin-when-cross-origin
- **CORS**: Configured for internal network access

### Access Control

- **Metrics Endpoint**: Restricted to internal networks
- **Health Checks**: No rate limiting
- **CORS**: Configurable origins

## Monitoring and Logging

### Access Logs

Custom log format includes:
- Remote address and user
- Request details and status
- Response size and timing
- Protocol version (HTTP/3, HTTP/2, HTTP/1.1)
- Proxy headers

### Health Checks

- **Angie Health**: Built-in Docker health check
- **Upstream Health**: Automatic failover to backup
- **Connection Health**: QUIC connection monitoring

### Metrics

Available through `/metrics` endpoint (internal networks only):
- Request counts and latencies
- Protocol distribution
- Upstream health status
- Connection statistics

## Troubleshooting

### Common Issues

1. **Certificate Errors**
   ```bash
   # Check certificate validity
   openssl x509 -in certs/cert.pem -text -noout
   ```

2. **QUIC Connection Issues**
   ```bash
   # Check UDP port availability
   netstat -an | grep :443

   # Check firewall rules
   sudo ufw status
   ```

3. **Upstream Connection Issues**
   ```bash
   # Check API server logs
   docker-compose logs api

   # Test direct API connection
   curl -k https://api:8443/healthz
   ```

### Debug Mode

Enable debug logging in Docker Compose:

```yaml
services:
  angie:
    environment:
      - NGINX_ENTRYPOINT_QUIET_LOGS=0
```

### Log Analysis

```bash
# Check Angie logs
docker-compose logs angie | grep -E "(error|warn)"

# Monitor real-time requests
docker-compose logs -f angie | grep -E "GET|POST"

# Check protocol distribution
docker-compose logs angie | grep -o "HTTP/[0-9.]*" | sort | uniq -c
```

## Requirements Compliance

This configuration implements the requirements from task 16:

### ✅ 3.1 - HTTP/3 End-to-End Support
- HTTP/3 over QUIC as primary protocol
- Graceful fallback to HTTP/2 and HTTP/1.1
- Alt-Svc headers for protocol negotiation

### ✅ 3.2 - HTTP/3 Fallbacks
- Automatic protocol negotiation
- Upstream failover configuration
- Connection migration support

### ✅ 3.3 - TLS Certificate Configuration
- TLS 1.3 for all encrypted connections
- OCSP stapling for certificate validation
- QUIC host key for connection migration
- Enhanced cipher suite configuration

## References

- [Angie Documentation](https://angie.software/en/)
- [HTTP/3 Specification (RFC 9114)](https://tools.ietf.org/html/rfc9114)
- [QUIC Specification (RFC 9000)](https://tools.ietf.org/html/rfc9000)
- [TLS 1.3 Specification (RFC 8446)](https://tools.ietf.org/html/rfc8446)

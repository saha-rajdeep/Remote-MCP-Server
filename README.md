# MCP Calculator Container

A containerized MCP (Model Context Protocol) server using FastMCP that provides a simple calculator tool for adding two numbers.

## Files

- `server.py` - FastMCP server with add_numbers tool
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container definition
- `k8s-deployment.yaml` - Kubernetes deployment and LoadBalancer service
- `build.sh` - Build script

## Building the Container

```bash
# Make build script executable (if not already)
chmod +x build.sh

# Build the Docker image
./build.sh
```

Or manually:
```bash
docker build -t mcp-calculator:latest .
```

## Running Locally

```bash
# Run the container locally
docker run -p 8000:8000 mcp-calculator:latest
```

The server will be available at `http://localhost:8000`

## Deploying to Amazon EKS

### Prerequisites
- AWS CLI configured with appropriate permissions
- kubectl installed
- Docker installed and running

### EKS Cluster Creation
The EKS cluster has been created using CloudFormation:
- **Cluster Name**: `mcp-calculator-cluster`
- **Region**: `us-west-2`
- **Stack**: `eks-mcp-calculator-cluster-stack`

### Container Image
The Docker image has been pushed to Amazon ECR:
```
279684395949.dkr.ecr.us-west-2.amazonaws.com/mcp-calculator:latest
```

### Deployment Steps

1. **Wait for EKS cluster to be ready** (15-20 minutes):
```bash
aws cloudformation describe-stacks --stack-name eks-mcp-calculator-cluster-stack --region us-west-2 --query 'Stacks[0].StackStatus'
```

2. **Deploy to EKS** (once cluster is ready):
```bash
./deploy-to-eks.sh
```

Or manually:
```bash
# Configure kubectl
aws eks update-kubeconfig --region us-west-2 --name mcp-calculator-cluster

# Deploy the application
kubectl apply -f k8s-deployment.yaml

# Check deployment status
kubectl rollout status deployment/mcp-calculator

# Get service information
kubectl get services mcp-calculator-service
```

3. **Get the LoadBalancer external IP**:
```bash
kubectl get services mcp-calculator-service -w
```

4. **Test the MCP server** (once external IP is available):
```bash
curl -s -H "Accept: text/event-stream" http://<EXTERNAL-IP>:8000/mcp/
```

### Deploying to Other Kubernetes Clusters

For non-EKS clusters, update the image in `k8s-deployment.yaml` to use a public registry or your own container registry, then:

```bash
kubectl apply -f k8s-deployment.yaml
```

## Testing the MCP Server

The server provides one tool:
- `add_numbers(a: float, b: float) -> float` - Adds two numbers together

### Testing with curl

The MCP server is currently deployed and accessible at:
```
http://k8s-default-mcpcalcu-7c00740636-3ed476afbba95187.elb.us-west-2.amazonaws.com/mcp/
```

#### Complete curl Test Workflow

**Step 1: Initialize MCP Session and Get Session ID**
```bash
SESSION_ID=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{"roots":{"listChanged":true},"sampling":{}},"clientInfo":{"name":"curl-test","version":"1.0.0"}}}' \
  http://k8s-default-mcpcalcu-7c00740636-3ed476afbba95187.elb.us-west-2.amazonaws.com/mcp/ \
  -D /dev/stderr 2>&1 | grep "mcp-session-id:" | cut -d' ' -f2 | tr -d '\r')

echo "Session ID: $SESSION_ID"
```

**Step 2: Send Initialization Notification (Required by MCP Protocol)**
```bash
curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
  http://k8s-default-mcpcalcu-7c00740636-3ed476afbba95187.elb.us-west-2.amazonaws.com/mcp/
```

**Step 3: List Available Tools (Optional)**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  http://k8s-default-mcpcalcu-7c00740636-3ed476afbba95187.elb.us-west-2.amazonaws.com/mcp/
```

**Expected Result:**
```json
event: message
data: {"jsonrpc":"2.0","id":2,"result":{"tools":[{"name":"add_numbers","description":"Add two numbers together.\n\nArgs:\n    a: First number to add\n    b: Second number to add\n    \nReturns:\n    The sum of a and b","inputSchema":{"type":"object","properties":{"a":{"type":"number"},"b":{"type":"number"}},"required":["a","b"]}}]}}
```

**Step 4: Call the add_numbers Tool**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"add_numbers","arguments":{"a":15.5,"b":24.3}}}' \
  http://k8s-default-mcpcalcu-7c00740636-3ed476afbba95187.elb.us-west-2.amazonaws.com/mcp/
```

**Expected Result:**
```json
event: message
data: {"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"39.8"}],"structuredContent":{"result":39.8},"isError":false}}
```

#### One-Liner Test (All Steps Combined)
```bash
SESSION_ID=$(curl -s -X POST -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{"roots":{"listChanged":true},"sampling":{}},"clientInfo":{"name":"curl-test","version":"1.0.0"}}}' http://k8s-default-mcpcalcu-7c00740636-3ed476afbba95187.elb.us-west-2.amazonaws.com/mcp/ -D /dev/stderr 2>&1 | grep "mcp-session-id:" | cut -d' ' -f2 | tr -d '\r') && echo "Session ID: $SESSION_ID" && curl -s -X POST -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -H "mcp-session-id: $SESSION_ID" -d '{"jsonrpc":"2.0","method":"notifications/initialized"}' http://k8s-default-mcpcalcu-7c00740636-3ed476afbba95187.elb.us-west-2.amazonaws.com/mcp/ && echo "Listing tools:" && curl -X POST -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -H "mcp-session-id: $SESSION_ID" -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' http://k8s-default-mcpcalcu-7c00740636-3ed476afbba95187.elb.us-west-2.amazonaws.com/mcp/ && echo "Calling add_numbers:" && curl -X POST -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -H "mcp-session-id: $SESSION_ID" -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"add_numbers","arguments":{"a":15.5,"b":24.3}}}' http://k8s-default-mcpcalcu-7c00740636-3ed476afbba95187.elb.us-west-2.amazonaws.com/mcp/
```

#### Test Different Numbers
To test with different numbers, change the `"a"` and `"b"` values in the final curl command:
```bash
# Example: Add 100 + 200
-d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"add_numbers","arguments":{"a":100,"b":200}}}'
```

#### Important Notes
- **Session Timeout**: Sessions expire after ~30-60 seconds due to FastMCP framework limitations
- **Rapid Execution**: Execute all steps quickly or use the one-liner command
- **MCP Protocol**: The `notifications/initialized` step is required by the MCP protocol after initialization

### Testing with MCP Client Libraries

You can also test using any MCP client or by making HTTP requests to the server endpoints.

## Kubernetes Resources

The deployment creates:
- **Deployment**: 2 replicas of the MCP calculator container
- **Service**: LoadBalancer type service exposing port 8000 externally
- **Resource limits**: 128Mi memory, 100m CPU per container
- **Resource requests**: 64Mi memory, 50m CPU per container

## Scaling

To scale the deployment:
```bash
kubectl scale deployment mcp-calculator --replicas=5
```

## Cleanup

To remove from Kubernetes:
```bash
kubectl delete -f k8s-deployment.yaml

#!/bin/bash

###############################################################################
# AWS CIEM Tool - Complete Cleanup Script
# 
# This script removes ALL local resources created by the CIEM tool:
# - Docker containers
# - Docker volumes (scan data)
# - Docker images
# - Docker networks
# - Log files
# - Generated reports
#
# WARNING: This does NOT delete any AWS resources. The CIEM tool only
#          reads AWS resources, it doesn't create them.
#
# Usage: ./scripts/cleanup.sh [--keep-data]
#        --keep-data: Keep scan data volumes (PostgreSQL, Neo4j, Redis)
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="aws-ciem-tool"
KEEP_DATA=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --keep-data)
            KEEP_DATA=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--keep-data]"
            exit 1
            ;;
    esac
done

echo -e "${YELLOW}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║         AWS CIEM Tool - Cleanup Script                     ║${NC}"
echo -e "${YELLOW}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Confirmation
echo -e "${YELLOW}This will remove:${NC}"
echo "  - All Docker containers (ciem-backend, ciem-frontend, ciem-postgres, ciem-neo4j, ciem-redis)"
echo "  - All Docker networks (ciem-network)"
echo "  - All Docker images for this project"
if [ "$KEEP_DATA" = false ]; then
    echo "  - All Docker volumes (scan data will be DELETED)"
else
    echo "  - Docker volumes will be PRESERVED"
fi
echo "  - Log files"
echo ""
echo -e "${RED}WARNING: This action cannot be undone!${NC}"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${GREEN}Cleanup cancelled.${NC}"
    exit 0
fi

echo -e "${GREEN}Starting cleanup...${NC}"
echo ""

# Step 1: Stop and remove containers
echo -e "${YELLOW}[1/6] Stopping Docker containers...${NC}"
if docker-compose ps -q 2>/dev/null | grep -q .; then
    docker-compose down
    echo -e "${GREEN}✓ Containers stopped${NC}"
else
    echo -e "${YELLOW}⚠ No running containers found${NC}"
fi
echo ""

# Step 2: Remove volumes (if not keeping data)
if [ "$KEEP_DATA" = false ]; then
    echo -e "${YELLOW}[2/6] Removing Docker volumes (scan data)...${NC}"
    
    volumes=(
        "${PROJECT_NAME}_postgres_data"
        "${PROJECT_NAME}_neo4j_data"
        "${PROJECT_NAME}_neo4j_logs"
        "${PROJECT_NAME}_redis_data"
        "${PROJECT_NAME}_backend_logs"
    )
    
    for volume in "${volumes[@]}"; do
        if docker volume ls -q | grep -q "^${volume}$"; then
            docker volume rm "$volume" 2>/dev/null && echo -e "${GREEN}✓ Removed volume: $volume${NC}" || echo -e "${YELLOW}⚠ Could not remove: $volume${NC}"
        fi
    done
else
    echo -e "${YELLOW}[2/6] Skipping volume removal (--keep-data flag)${NC}"
fi
echo ""

# Step 3: Remove Docker images
echo -e "${YELLOW}[3/6] Removing Docker images...${NC}"
images=$(docker images --filter=reference="*ciem*" -q)
if [ -n "$images" ]; then
    echo "$images" | xargs docker rmi -f 2>/dev/null && echo -e "${GREEN}✓ Images removed${NC}" || echo -e "${YELLOW}⚠ Some images could not be removed${NC}"
else
    echo -e "${YELLOW}⚠ No CIEM images found${NC}"
fi
echo ""

# Step 4: Remove Docker networks
echo -e "${YELLOW}[4/6] Removing Docker networks...${NC}"
if docker network ls | grep -q "ciem-network"; then
    docker network rm ciem-network 2>/dev/null && echo -e "${GREEN}✓ Network removed${NC}" || echo -e "${YELLOW}⚠ Network could not be removed${NC}"
else
    echo -e "${YELLOW}⚠ No CIEM network found${NC}"
fi
echo ""

# Step 5: Clean up log files
echo -e "${YELLOW}[5/6] Cleaning up log files...${NC}"
if [ -d "backend/logs" ]; then
    rm -rf backend/logs/*
    echo -e "${GREEN}✓ Backend logs cleaned${NC}"
else
    echo -e "${YELLOW}⚠ No backend logs found${NC}"
fi
echo ""

# Step 6: Clean up node_modules (optional)
echo -e "${YELLOW}[6/6] Cleaning up node_modules (optional)...${NC}"
read -p "Do you want to remove frontend/node_modules? (yes/no): " -r
echo ""
if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    if [ -d "frontend/node_modules" ]; then
        rm -rf frontend/node_modules
        echo -e "${GREEN}✓ node_modules removed${NC}"
    else
        echo -e "${YELLOW}⚠ node_modules not found${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Skipping node_modules cleanup${NC}"
fi
echo ""

# Summary
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                  Cleanup Complete!                         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}All local CIEM tool resources have been removed.${NC}"
echo ""
echo -e "${YELLOW}Note: This script only removes local Docker resources.${NC}"
echo -e "${YELLOW}Your AWS resources remain untouched.${NC}"
echo ""

# Show remaining Docker resources
echo -e "${YELLOW}Remaining Docker resources:${NC}"
echo "Containers: $(docker ps -a | grep -c ciem || echo 0)"
echo "Volumes: $(docker volume ls | grep -c ciem || echo 0)"
echo "Images: $(docker images | grep -c ciem || echo 0)"
echo ""

echo -e "${GREEN}To reinstall the CIEM tool, run:${NC}"
echo "  docker-compose up -d"
echo ""

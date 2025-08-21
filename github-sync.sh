#!/bin/bash

set -e  # Exit on any error

# Configuration
GITHUB_SSH_URL="git@github.com:aws/aws-eks-best-practices.git"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper function for printing status messages
print_status() {
    echo -e "${GREEN}==>${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}Warning:${NC} $1"
}

print_error() {
    echo -e "${RED}ERROR:${NC} $1"
    exit 1
}

# Check if we're in a git repository
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    print_error "Not in a git repository"
fi

# Check for origin remote
if ! git remote | grep -q "^origin$"; then
    print_error "Remote 'origin' not found"
fi

# Check for GitHub remote, add if missing
if ! git remote | grep -q "^github$"; then
    print_status "GitHub remote not found. Adding it..."
    if ! git remote add github "$GITHUB_SSH_URL"; then
        print_error "Failed to add GitHub remote"
    fi
fi

# Verify remote configurations
print_status "Verifying remote configurations..."
github_url=$(git remote get-url github 2>/dev/null || echo "")
if [[ "$github_url" != *"github.com"* ]]; then
    print_error "GitHub remote does not point to GitHub. Current: $github_url"
fi

origin_url=$(git remote get-url origin 2>/dev/null || echo "")
if [[ "$origin_url" != *"amazon.com"* ]]; then
    print_error "Origin remote does not point to Amazon internal. Current: $origin_url"
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    print_error "You have uncommitted changes. Please commit or stash them before syncing."
fi

# Fetch from both remotes
print_status "Fetching from origin (Amazon internal)..."
if ! git fetch origin; then
    print_error "Failed to fetch from origin remote"
fi

print_status "Fetching from GitHub..."
if ! git fetch github; then
    print_error "Failed to fetch from GitHub remote"
fi

# Update mainline branch from origin
print_status "Updating mainline branch from origin..."
if ! git checkout mainline; then
    print_error "Failed to checkout mainline branch"
fi

if ! git merge origin/mainline --ff-only; then
    print_error "Failed to fast-forward mainline from origin. Manual intervention required."
fi

# Update master branch from GitHub
print_status "Updating master branch from GitHub..."
if ! git checkout master; then
    print_error "Failed to checkout master branch"
fi

if ! git merge github/master --ff-only; then
    print_error "Failed to fast-forward master from GitHub. Manual intervention required."
fi

# Switch back to mainline and merge master
print_status "Switching to mainline and merging master..."
if ! git checkout mainline; then
    print_error "Failed to checkout mainline branch"
fi

if ! git merge master --no-edit; then
    print_error "Merge conflicts detected between master and mainline. Please resolve manually."
fi

# Push mainline to origin
print_status "Pushing mainline to origin..."
if ! git push origin mainline; then
    print_error "Failed to push mainline to origin"
fi

print_status "Successfully synced: GitHub master -> local master -> mainline -> origin"

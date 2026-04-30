#!/bin/bash
set -e

echo '=== [1/3] Setting up 3GB swap ==='
if [ ! -f /swap.img ]; then
  fallocate -l 3G /swap.img
  chmod 600 /swap.img
  mkswap /swap.img
  swapon /swap.img
  grep -q '/swap.img' /etc/fstab || echo '/swap.img none swap sw 0 0' >> /etc/fstab
  echo 'Swap created.'
else
  echo 'Swap already exists, skipping.'
fi
free -h

echo '=== [2/3] Installing Docker ==='
if ! command -v docker &>/dev/null; then
  apt-get update -qq
  apt-get install -y -qq ca-certificates curl gnupg
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  . /etc/os-release
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" > /etc/apt/sources.list.d/docker.list
  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  systemctl enable docker
  systemctl start docker
  echo 'Docker installed.'
else
  echo 'Docker already installed, skipping.'
fi
docker --version
docker compose version

echo '=== [3/3] Cloning repo ==='
if [ ! -d /opt/aihr ]; then
  git clone https://github.com/stevechen1112/aihr.git /opt/aihr
  echo 'Repo cloned.'
else
  cd /opt/aihr && git pull origin main
  echo 'Repo already exists, pulled latest.'
fi
cd /opt/aihr && git log --oneline -3

echo '=== Server setup complete ==='

# VPS Visual Browser Setup with VNC

## Install Desktop Environment on VPS

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install lightweight desktop environment
sudo apt install -y ubuntu-desktop-minimal

# Install VNC server
sudo apt install -y tightvncserver

# Install Firefox/Chrome
sudo apt install -y firefox

# Start VNC server
vncserver :1 -geometry 1920x1080 -depth 24

# Set VNC password when prompted
```

## Configure VNC Access

```bash
# Edit VNC startup script
nano ~/.vnc/xstartup

# Add this content:
#!/bin/bash
xrdb $HOME/.Xresources
startxfce4 &
```

## Access from Windows

1. Download VNC Viewer
2. Connect to: your-vps-ip:5901
3. Enter VNC password
4. You'll see desktop environment

## Enable Visual Mode in Production

```python
# In .env.production, add:
ENABLE_VISUAL_MODE=true
```

## Modify Code to Allow Visual in Production

```python
# In instagram_daily_post.py
is_production = os.environ.get('ENVIRONMENT') == 'production'
allow_visual_in_prod = os.environ.get('ENABLE_VISUAL_MODE') == 'true'
headless_mode = True if (is_production and not allow_visual_in_prod) else not self.visual_mode
```

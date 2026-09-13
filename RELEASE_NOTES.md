# Playground 0.5.1 · Plasma window icon

- Explicitly set Playground's GTK icon and window identity to match its desktop launcher.
- Use the installed SVG's absolute path in the desktop entry so Plasma does not depend on a stale icon-theme cache.
- Refresh launcher and icon metadata when the installed app starts, including after an in-app update.
- Preserve the existing Start at login setting during metadata repair.

Update through **Check for updates → Update & restart**.

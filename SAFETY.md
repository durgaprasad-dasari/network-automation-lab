# Safety Rules (read before every lab)

1. Use mock data first, then simulators or lab devices you are authorized to use.
2. Never run a configuration-changing script against a production device.
3. Start read-only: `show` commands only. Config changes need backup, validation, and your explicit approval.
4. Never hardcode passwords, tokens, or keys. Use environment variables or `.env` (listed in `.gitignore`).
5. Never commit `.env`, private keys, real IPs from an employer, or real device configs to GitHub.
6. AWS: prefer read-only calls. Check the current Free Tier terms on aws.amazon.com before creating anything, and delete resources after each lab.

# Moving Intelligence Device Tracker Component
This integration supports Moving Intelligence objects as device tracker in Home Assistant

NOTE: You need an account and api-key for https://movingintelligence.com/

## Installation

### HACS - Recommended
- Have [HACS](https://hacs.xyz) installed, this will allow you to easily manage and track updates.
- Add this repo to your HACS installation.
- Search for 'Moving Intelligence'.
- Click Install below the found integration.
- Restart Home-Assistant.

### Manual
- Copy directory `custom_components/moving_intelligence` to your `<config dir>/custom_components` directory.
- Restart Home-Assistant.

## Configuration
Search and install the 'Moving Intelligence' integration via Configuration > Devices & Services, and fill in your username and API key.

Each vehicle becomes a device with a GPS `device_tracker` entity, polled every minute. Trip, odometer and address details are available as attributes. Vehicles added to your account later are picked up automatically.

If your API key changes or is revoked, Home Assistant shows a re-authentication prompt where you can enter the new key.

## Development

```bash
pip install -r requirements.txt -r requirements_lint.txt
scripts/test
pre-commit run --all-files --hook-stage manual --config .github/pre-commit-config.yaml
```

## Community

Questions, ideas or just want to chat? Join The Junkyard on Discord:

<a href="https://discord.gg/hUBQxRhJCU">
  <img src="https://raw.githubusercontent.com/cyberjunky/cyberjunky/main/assets/junkyard-discord.svg"
       alt="Join The Junkyard on Discord" width="600">
</a>


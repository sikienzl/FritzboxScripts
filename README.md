# FritzboxScripts

[![CLI Check](https://github.com/sikienzl/FritzboxScripts/actions/workflows/cli-check.yml/badge.svg?branch=master)](https://github.com/sikienzl/FritzboxScripts/actions/workflows/cli-check.yml)

A collection of python scripts for interacting with a Fritz!Box, especially for features that cannot be accessed via the TR064 protocol. 

## Features

- List all call forwarding rules
- Toggle a specific rule by ID
- Uses `.env` file for configuration

## Setup

1. **Create a virtual environment (recommended):**
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Copy `.env.example` to `.env` and fill in your Fritz!Box credentials.**

   - **Note:** The `FRITZ_USER` usually starts with `fritz` followed by 4 digits, e.g. `fritz1234`.  
     If you are unsure, run `python fritzbox_user_list.py` to list all available Fritz!Box users.

3. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

## Usage

1. **List all call forwarding rules:**
   ```
   python fritzbox_call_forwarding.py --list
   ```

2. **Toggle a rule:**
   ```
   python fritzbox_call_forwarding.py --rule-id rub_2
   ```
   If `FRITZ_DEFAULT_RULE_ID` is set in `.env`, you can omit `--rule-id`.

## Configuration

Create a `.env` file in the project directory:

```
FRITZ_IP=192.168.178.1
FRITZ_USER=fritz1234
FRITZ_PASS=your_password
FRITZ_DEFAULT_RULE_ID=rub_2
```

## Compatibility

This code was tested with a **FRITZ!Box 7490** running firmware version **7.62**.  
Other models or firmware versions may behave differently.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

**Note:**  
Never commit your real `.env` file or credentials to a public repository!
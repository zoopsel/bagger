# Bagger

Grabs newly released articles of yesterday and sends them to the configured email.

## Installation

Create a Python virutal environment `python3.14 -m venv .venv`.
Activate environment `source /.venv/bin/activate`.
Install dependencies `pip install -r requirements.txt`.

## Usage

Copy the configuration template (`config_template.toml`) and rename it to `config.toml`.
Fill in the variables (`email_cc` is optional and can be left as is). 
Run the application using `python bagger.py`.

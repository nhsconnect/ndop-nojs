#!/usr/bin/env python3

from ndopapp import create_app

app = create_app("ndopapp.config.Config")

if __name__ == '__main__':
    app.run()

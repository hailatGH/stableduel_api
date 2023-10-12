# Debugging

This project comes mostly preconfigured for debugging however there are a few things you need to do in order to debug your local instance.

## Running the Django server in debug mode
Running the Django server for debugging is a little different than how you would normally run the server. To run the Django server for debugging use the following:
```
docker compose -f docker-compose.debug.yml up
```

## Attach VSCode to remote instance
To attach VSCode to the remote instance simply open the debug panel and select the green play button on the top of the panel (ensure "Python: Remote Attach" is selected). Once VSCode has attached successfully the background color of the bottom information bar will change to orange.



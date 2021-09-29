## How to deploy the dashboard as an Azure web app

### Get an account on Dockerhub

Following instructions [here](https://docs.docker.com/docker-hub/)


### Build the docker image and push to Dockerhub

```
docker build -t <DOCKER_ID>/gappadash:latest .
docker push <DOCKER_ID>/gappadash:latest
```

### Create Azure web app on the Azure portal

* Go to [Azure portal](https://portal.azure.com)
* Click "+ Create a resource", and choose "Web App".
* Choose subscription, choose or create a resource group, and pick a name (needs to be unique within all Azure webapps).
* In the "publish" field, choose "Docker Container", then "Linux" operating system.
* At the bottom of the page, it will fill in a default name for a new App Service Plan - this is normally fine.   You can also choose the "size" - possibly go for a smaller/cheaper one than the default (at least for testing), e.g. "B1".
* Click "Next:Docker".
* Leave "Options" as the default value, change "Image Source" to "Docker Hub", and fill in the name of your docker image (i.e. "<DOCKER_ID>/gappadash:latest") in the "Image and tag" field.  You can leave the "startup command" blank.
* Click "Review and Create", and assuming it's happy, click "Create".
* The app will take a couple of minutes to deploy, then the webpage will say "Deployment is complete", and give you a link to "Go to resource" - click this.
* Click on "Configuration" on the left sidebar, and click "+ New application setting".  Add a setting called "WEBSITES_PORT", with value "8050:80", and save it.
* Go back to "Overview" at the top of the left sidebar.  You can stop or restart the webapp from here - probably good to restart it after changing settings.
You can also see the URL here, and click on it.
* Note that it will typically take up to 10 mins after you first set it up before your web-app is accessible.   If you go to the page before that, you might see "loading", or you might get 502 errors.  Keep refreshing every couple of minutes.   If it doesn't work after 10 mins, probably something went wrong.  You can try looking at the "Log stream" under "Monitoring" in the left sidebar in the portal.

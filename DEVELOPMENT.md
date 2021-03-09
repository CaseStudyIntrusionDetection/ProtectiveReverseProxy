# Development

There exists a docker-compose file directly made for the development on PRP. 
Just run `docker-compose -f docker-compose.dev.yml up` to start PRP using this file.
Since we do development, this file won't use the image from Docker Hub and hence build it 
locally. 

PRP will start in the same mode as always, but the directories `proxy` and `protection`
are directly bind-mounted into the container. Changes of files on the host will be directly
available in the container. Of course, the PRP core does not look for changes of source files
regularly, such that we have to start it in development mode. (Or just restart the Docker container while we 
do not have to rebuild cause we bind-mounted the changed files.)

## Starting the PRP core in development mode
1. Run `docker-compose -f docker-compose.dev.yml up --build` in git repository's root
2. Open a shell in the container `docker-compose -f docker-compose.dev.yml exec --user www-data protection_proxy bash`
3. Navigate `cd /proxy/`
4. Start the PRP core in development mode `flask run --host=0.0.0.0 --port=5000 --reload`
5. The PRP core will reload when a python source was changed.
6. The PRP core is accessible at `http://localhost:5000`

**Attention**:
- The development mode runs less stable.
- There is no routing through NGINX.
- An approved request will only show `Requests approved` and not the protected application.

## Changing other files (than Python source)
The container will have to be rebuild after each change when a file in `conf`
was changed. It will crash when there are errors in one of these files.
Of course, changes of the `Dockerfile` will require a rebuild.

**Hints**:
- Use the PRP core log at `/tmp/prp.log`
- Use the NGINX log at `/var/log/nginx/error.log`
- Take a look at the messages of `supervisord` (printed on STDOUT)

## :wink:
Please take a look a the currently used practices and styles in the 
source code before contributing to the project.

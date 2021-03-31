# OntoTransCoreComponents
This repository contains the OntoTrans WP3 development.

# Stardog Installation and Possible Deployments
For the scope of OntoTrans Core components, we explore two deployment alternatives for the Stardog Triplestore, i.e. either as a Docker-containerised instance or as an instance running on a Virtual Machine (VM).
In this phase, these two deployments can be considered equivalent; probably the dockerized one may be preferable for someone that would like to quickly experiment with Stardog (e.g., in Windows OS) without having to directly use a Linux-based OS or having to deal with VMs.
Here, we briefly detail the installation of Stardog inside a Docker container and inside a VM. 

## Dockerized Stardog in Windows
Open the Windows PowerShell as administrator, then:
1.	Check to have Docker installed, otherwise download and install it. (e.g., https://docs.docker.com/docker-for-windows/install/):

    $ docker --version
    
2.	Retrieve the (latest) Stardog image:

    $ docker pull stardog/stardog:latest
    
3.	Just list the Docker images to make sure all is fine:

    $ docker image ls
    
4.  Run the pulled Stardog image:

    $ docker run -it --name here_the_container_name -p 5820:5820 stardog/stardog:latest

    --name assigns a memorable name to the container you are running-
    -p maps port 5820 on the container (the default Stardog port) to port 5820 on localhost for easy communication.
    The last argument (i.e., stardog/stardog:latest) just tells which image you run.
    Then, you are asked for a license. With three consecutive “yes” (i.e., “y”), and by inserting an academic e-mail (e.g., name.surname@unibo.it) you receive a 1-year trial   license. 
    
From this moment, you are able to use Stardog .

## Stardog on VM
With the only requirement of the OpenJDK (or Oracle Java) 8 or 11, it’s also possible to install Stardog as a system service either in Microsoft Windows or Linux-like (Debian or RPM based) system: our test has involved a VM with Kubuntu 18.04 x64. By adding the gpg key we are ready to let apt install any version of Stardog:

    $ curl http://packages.stardog.com/stardog.gpg.pub | apt-key add

    $ echo "deb http://packages.stardog.com/deb/ stable main" >> /etc/apt/sources.list

    $ apt-get update

    $ apt-get install -y stardog[=<version>]

Now we are ready to start Stardog for the first time, manually, because we need to license the software like in Docker installation. This is done by executing the stardog-server.sh script in /opt/stardog and following the prompted instructions. This brings up the service on the default port (5820) on the local machine, letting the Studio web-app to connect with the default credentials. Now the system is up and systemctl can manage it as any other system service.
Once Stardog is installed and running at, e.g. 192.168.x.x:5820, it can be SPARQL queried via its REST APIs. 

## Import toolchain for Stardog
The import toolchain, i.e. e2s.py, to populate the the Stardog Triplestore takes in input the source ontology (that can be a URI or a filepath for the entry file of the ontology with all of the import), runs the Fact++ reasoner  on it, and imports in Stardog – that should be running in the meanwhile – the inferred ontology. From this moment, it should be populated as desired. 

For now, the toolchain is developed as a bash script.  

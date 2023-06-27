# eVOLVER DPU Test Server
Test Server developed for communications tests for the new CNPEM eVOLVER software.

## Running the Test Server

---

### Install Requirements

Firstly, once in the project folder, install the requirements of this server running:

    $ pip install -r requirements.txt

### Uvicorn

This test runs on [Uvicorn](https://www.uvicorn.org/) ASGI web server implementation for Python. To run the server on localhost:

    $ uvicorn --reload evolver_server:app --port=8081

If it is needed to expose the port to other devices, the following code will expose the IP of your server computer with the selected port:

    $ uvicorn --reload evolver_server:app --host 0.0.0.0 --port=8081

**The port 8081 is a default port of the eVOLVER DPU, which is the study object of this repository.**

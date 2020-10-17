### Setup project on Linux / OS X

##### 1\. Install [docker](https://docs.docker.com/get-docker/):
    
- First, uninstall old versions: 
    ```bash
    sudo apt-get remove docker docker-engine docker.io containerd runc
    ```

- Add Docker's official GPG key:
  ```bash
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
  ```

- Set up Docker **stable** repository:
  ```bash
  sudo add-apt-repository \
     "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) \
      stable"
  ```
- Install **Docker Engine**:
  ```bash
  sudo apt-get update && sudo apt-get install docker-ce docker-ce-cli containerd.io
  ```
- [After installation](https://docs.docker.com/engine/install/linux-postinstall/) you have to create `docker` group and add your user:
  ```bash
  sudo groupadd docker
  sudo usermod -aG docker $USER
  ``` 
- You can find more [details here](https://docs.docker.com/engine/install/ubuntu/). 

##### 2\. Setup enviroment:
   - clone repository:
   ```bash
    git clone XXX & cd YYY
   ```  
   - rename `.env.dev-sample` to `.env.dev`

   - create docker containers:
   ```bash
   docker-compose up -d --build
   ```
   - run docker containers:
   ```bash
   docker-compose up
   ```
   - migrate database
   ```bash
   docker-compose exec web python manage.py migrate
   ```
   - open second terminal and generate developers demo:
   ```bash
   docker-compose exec web python manage.py generate_demo
   ```

##### 3\. Try:
    - open `localhost:8080/admin` on your web browser and try login to demo account.
    
     
   
   
  
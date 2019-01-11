# Stemerald
Digital currency trading wrapper


Setting up development Environment on Linux
----------------------------------

### Installing Dependencies

    $ sudo apt-get install libass-dev libpq-dev postgresql \
        build-essential redis-server redis-tools

### Setup Python environment

    $ sudo apt-get install python3-pip python3-dev
    $ sudo pip3 install virtualenvwrapper
    $ echo "export VIRTUALENVWRAPPER_PYTHON=`which python3.6`" >> ~/.bashrc
    $ echo "alias v.activate=\"source $(which virtualenvwrapper.sh)\"" >> ~/.bashrc
    $ source ~/.bashrc
    $ v.activate
    $ mkvirtualenv --python=$(which python3.6) --no-site-packages stemerald

#### Activating virtual environment
    
    $ workon stemerald

#### Upgrade pip, setuptools and wheel to the latest version

    $ pip install -U pip setuptools wheel
  
### Installing Project (edit mode)

So, your changes will affect instantly on the installed version

#### nanohttp

    $ cd /path/to/workspace
    $ git clone git@github.com:pylover/nanohttp.git
    $ cd nanohttp
    $ pip install -e .
    
#### restfulpy
    
    $ cd /path/to/workspace
    $ git clone git@github.com:pylover/restfulpy.git
    $ cd restfulpy
    $ pip install -e .

#### stemerald
    
    $ cd /path/to/workspace
    $ git clone git@github.com:Carrene/stemerald.git
    $ cd stemerald
    $ pip install -e .
    
#### Enabling the bash auto completion for stemerald

    $ echo "eval \"\$(register-python-argcomplete stemerald)\"" >> $VIRTUAL_ENV/bin/postactivate    
    $ deactivate && workon stemerald
    
### Setup Database

#### Configuration

Create a file named `~/.config/stemerald.yml`

```yaml

db:
  uri: postgresql://postgres:postgres@localhost/stemerald_dev
  test_uri: postgresql://postgres:postgres@localhost/stemerald_test
  administrative_uri: postgresql://postgres:postgres@localhost/postgres
   
   
```

#### Remove old abd create a new database **TAKE CARE ABOUT USING THAT**

    $ stemerald admin create-db --drop --basedata --mockup

#### Drop old database: **TAKE CARE ABOUT USING THAT**

    $ stemerald [-c path/to/config.yml] admin drop-db

#### Create database

    $ stemerald [-c path/to/config.yml] admin create-db

Or, you can add `--drop` to drop the previously created database: **TAKE CARE ABOUT USING THAT**

    $ stemerald [-c path/to/config.yml] admin create-db --drop
    
#### Create database object

    $ stemerald [-c path/to/config.yml] admin setup-db

#### Database migration

    $ stemerald migrate upgrade head

#### Insert Base data

    $ stemerald [-c path/to/config.yml] admin base-data
    
#### Insert Mockup data

    $ stemerald [-c path/to/config.yml] dev mockup-data
    
### Unittests

    $ nosetests
    
### Serving

- Using python builtin http server

```bash
$ stemerald [-c path/to/config.yml] serve
```    

- Gunicorn

```bash
$ ./gunicorn
```

Setting up development Environment on Windows (Tested for Windows 10)
----------------------------------

### Setup Python environment
- Install Python on Windows (https://www.python.org/downloads/) and make sure the Scripts subdirectory of Python is in your PATH.
   For example, if python is installed in C:\Python35-32\,
   you should make sure C:\Python35-32\Scripts is in your PATH in addition to C:\Python35-32\.

- Install related Microsoft Visual C++ Build Tools according to your python version mentioned on [WindowsCompilers](https://wiki.python.org/moin/WindowsCompilers)
- Run the following command on a Command Prompt to install Virtual Environment Wrapper for Windows:

```
    > pip install virtualenvwrapper-win
```


- Add WORKON_HOME variable as an Environment Variable and set the value %USERPROFILE%\Envs by default.

- Run the following command to make a Virtual Environment for "stemerald" :

```
    > mkvirtualenv stemerald
```

#### Activating virtual environment

    > workon stemerald

#### Upgrade pip, setuptools and wheel to the latest version

    (stemerald) > pip install -U pip setuptools wheel

### Installing Project in Virtual Environment(edit mode)

So, your changes will affect instantly on the installed version

#### restfulpy

    (stemerald) > cd path/to/stemerald/..
    (stemerald) > git clone git@github.com:pylover/restfulpy.git
    (stemerald) > cd restfulpy
    (stemerald) > pip install -e .

    (stemerald) > cd path/to/stemerald/..
    (stemerald) > git clone git@github.com:pylover/nanohttp.git
    (stemerald) > cd nanohttp
    (stemerald) > pip install -e .

    (stemerald) > cd /path/to/stemerald
    (stemerald) > pip install -e .

### Setup PostgreSQL
You can find the windows installer on https://www.postgresql.org/download/windows/

### Setup Database

- Create the stemerald.yml file in %USERPROFILE%\AppData\Local
- Add the following lines to this file
```
    db:
      uri: postgresql://postgres:postgres@localhost/stemerald_dev
      administrative_uri: postgresql://postgres:postgres@localhost/postgres
      test_uri: postgresql://postgres:postgres@localhost/stemerald_test
      echo: true
```

#### create database **TAKE CARE ABOUT USING THAT**

    (stemerald) /path/to/stemerald > stemerald admin create-db --drop --basedata

#### Drop old database: **TAKE CARE ABOUT USING THAT**

    (stemerald) /path/to/stemerald > stemerald -c path/to/stemerald.yml admin drop-db

#### Create database

    (stemerald) /path/to/stemerald > -c path/to/stemerald.yml admin create-db

Or, you can add `--drop` to drop the previously created database: **TAKE CARE ABOUT USING THAT**

    (stemerald) /path/to/stemerald > stemerald -c path/to/stemerald.yml admin create-db --drop

#### Create database object

    (stemerald) /path/to/stemerald > stemerald -c path/to/stemerald.yml admin setup-db

#### Database migration

    (stemerald) /path/to/stemerald > stemerald migrate upgrade head

#### Insert Base data

    (stemerald) /path/to/stemerald > stemerald -c path/to/stemerald.yml admin base-data

#### Insert Mockup data

    (stemerald) /path/to/stemerald > stemerald -c path/to/stemerald.yml dev mockup-data

### Unittests
This command will generate the Mark-Down documents which are needed for Front-end developers :

    (stemerald) /path/to/stemerald > nosetests

### Serving

- Using nanohttp server

```
    (stemerald) /path/to/stemerald > stemerald serve
```


Deployment
----------------------------------

Run this command for initialization (only first time):

    $ ./scripts/install-requirements.sh
    
Then you should make your `variables.sh` file. You can inspire from `variables.sh.example` file:

    $ cp scripts/variables.sh.example scripts/variables.sh
    $ nano scripts/variables.sh
    $ (modify whatever you want...)
    
Also do it for `config.yml.example` to create the `config.yml` file:

    $ cp scripts/config.yml.example scripts/config.yml
    $ nano scripts/config.yml
    $ (modify whatever you want...)
    
Run this command for installation:

    $ ./scripts/install.sh
    
**Do not forget to modify the configuration file.**

Changelog
----------------------------------

#### 0.7.2
* Order presentation API added

#### 0.7.1
* Get invitation by id
* Get invitation list 
* Create invitation
* invitation_code_required field added to membership configurations
* Activate/Deactivate invitation added
* Edit invitation added
* invitationCode field added to registration API


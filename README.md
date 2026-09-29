# en-crypter

An encrypted and **UNCONVENTIONAL** way to save the data on the Internet's free to upload and no-limit sites rather than paying for the storage and the services.

Encrypter is a local-first containerized *(will soon be containerized)* software that can be used to encrypt the data and store it in different formats, on platforms like SoundCloud, YT, or even Pinterest *(jus one thing, wherever you store, jus keep in mind, data is not COMPRESSED and stored- as it could lead to some errors - and for the `v1` - error correction is not yet present)*.

## EVERY MODULE AND ITS CODE
Find in the below table about the working and the code of each of the module. Make tweaks acc to your choice and read the `README.md` of each module.
| Module Name | Description | Link |
| :--- | :--- | :--- |
| `text-to-morse-video` | Convert text to morse code and encode in video | [📁 Directory](./text-to-morse-video) |
| `text-to-image` | Convert text to image with encryption | [📁 Directory](./text-to-image) |

## GETTING STARTED
### DOCKERIZED VERSION

### CLONE AND RUN LOCALLY
In order to run this locally, simply do the following-
```bash
# for ssh based- copy this:
git clone git@github.com:Th3C0d3Mast3r/en-crypter.git

# for HTTP based- copy this:
git clone https://github.com/Th3C0d3Mast3r/en-crypter.git

# Once cloned, run the following:-
python -m .venv venv
python bin/activate/venv
pip install -r requirements.txt
cd frontend && npm i

# Now, for each of the following subdirectories, copy the .env.sample to .env
cd  text-to-morse-video && cp .env.sample .env
cd text-to-image && cp .env.sample .env
# and so on . . . . 
```

> [!NOTE]
> Change the default things in the .env so that, the encrypted files are unique! 

Once this is cloned, now, to run, start the backend server and then, start the frontend service-
```bash
# From the repo base, run-
python api_server.py

# On a different terminal, run-
npm run dev

# the frontend is exposed to the port 3000. To change this, make changes in the code!
```


## HOW ITS WORKING
So, the current modules of `text-to-morse-video` and the `text-to-image` work on the below flow-
[flow goes here]

## CONTRIBUTING GUIDELINES

## 
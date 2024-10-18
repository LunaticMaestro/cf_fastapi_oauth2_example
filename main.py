'''Entrypoint file for standard or simple fastapi application.
'''

# Generic Libraries 
from fastapi import FastAPI, File, HTTPException, BackgroundTasks, UploadFile, Request
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

# Important libraries 
import os
from typing import Annotated
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from cfenv import AppEnv    # This is Un-official library, but recommened by official sap package: https://pypi.python.org/pypi/cfenv
                            #   alternatively you can use environment variables, See source code: https://github.com/jmcarp/py-cfenv/blob/797057345393b74b8df21b145d784f38c1d565a5/cfenv/__init__.py#L16          

from sap import xssec       # This is required to match the incoming token with XSUAA service token


# Generic fastapi handler
app = FastAPI()

# Handler for CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Kindly fix it as per your requirements
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

### Required ### 
oauth2_scheme = HTTPBearer()


### Required: Handle CF Authentication ### 
async def check_authentication(
        token: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)], 
    ) -> None:
    '''Checks the authentication against SAP security broker
    
    All the blocks raises error when authentication is failed therefore blocked of other functions related down the hierarchy.
    When authentication, the function returns None.
    '''
    local_debug = os.environ.get("LOCAL_DEBUG", 'false')
    if local_debug.lower() == 'true':
        return True
    else: 
        print("Using authentication; if local testing set environment `LOCAL_DEBUG=TRUE` ")
        # Security Credentials fetch
        env = AppEnv()
        xsuaa_service_name = 'my_xsuaa_1' # [modifiable] Important name of the xsuaa application, you will bind the same xsuaa app to this app, see read me.
        #
        # usual handling of token validation
        uaa_service = env.get_service(name=xsuaa_service_name) 
        if uaa_service is not None: 
            uaa_service_creds: dict = uaa_service.credentials
            security_context = xssec.create_security_context(token.credentials, uaa_service_creds)
            isAuthorized = security_context.check_scope('uaa.resource')
            if not isAuthorized:
                raise HTTPException(status_code=403, detail="Authorization header missing")
        else:
            raise HTTPException(status_code=503, detail=f'''
                Possible Issue:
                    - Not able to find the service credentials for service: {xsuaa_service_name} in environment 
                    - Set local_debug = False in function `check_authentication` for local debugging.
            ''')
    return None

#### Paths ####
@app.get("/health")
def get_health():
    '''Checks if this whole application is reachable'''
    return {"status": "ok"}

@app.get

@app.get("/data_read")
def data_read(
    request: Request, 
    authenticate: Annotated[str, Depends(check_authentication)]   # un-used variable
    ):
    '''Returns some data when you pass correct authorization'''
    return {"message": "you see this when you pass through authorization."}

# Main entry point for running the app
if __name__ == "__main__":
    # UNCOMMENT FOR local debugging
    # os.environ['LOCAL_DEBUG'] = 'true'  
    #
    # Run the FastAPI app using Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
import requests
import msal
import pandas as pd 

def declare_app(app_id, tenant_id):
    app = msal.PublicClientApplication(
    app_id, authority=f"https://login.microsoftonline.com/{tenant_id}")
    return app

def azure_login(app_id:str="ea0616ba-638b-4df5-95b9-636659ae5121", tenant_id:str)->list[str]:
    """
    Login via user principal, using login and password to Microsoft PBI account. Browser window will be prompted. By default use and Microsoft Public app_id. 
    """

    app = declare_app(app_id, tenant_id)
    result = None
    accounts = app.get_accounts()

    if accounts:
        print("Account(s) already signed in:")
        for a in accounts:
            print(a["username"])
        chosen = accounts[0]  # Assuming the end user chose this one to proceed
        print("Proceed with account: %s" % chosen["username"])
        # Now let's try to find a token in cache for this account
        result = app.acquire_token_silent(["https://analysis.windows.net/powerbi/api/.default"], account=chosen)

    if not result:
        print("A local browser window will be open for you to sign in. CTRL+C to cancel.")
        result = app.acquire_token_interactive(  # Only works if your app is registered with redirect_uri as http://localhost
            ["https://analysis.windows.net/powerbi/api/.default"],
        #parent_window_handle=...,  # If broker is enabled, you will be guided to provide a window handle
        #prompt=msal.Prompt.SELECT_ACCOUNT,  # Or simply "select_account". Optional. It forces to show account selector page
        #prompt=msal.Prompt.CREATE,  # Or simply "create". Optional. It brings user to a self-service sign-up flow.
            # Prerequisite: https://docs.microsoft.com/en-us/azure/active-directory/external-identities/self-service-sign-up-user-flow
        )
    return result

def apicall_daxquery(semantid_model_id: str, login_response: list['str'], dax_query: str) -> pd.DataFrame: 
    """
    Call REST API to run DAX query against chosen semantic model. You must authenticate via login and password - you are providing token  which can be used 8 min after login. 
    """

    api_url = f"https://api.powerbi.com/v1.0/myorg/datasets/{semantid_model_id}/executeQueries"
    body = {
  "queries": [
    {
      "query": dax_query
    }
  ],
  "serializerSettings": {
    "includeNulls": True
  }}
    
    response = requests.post(url=api_url, 
        headers=
            {
                "Authorization": f"Bearer {login_response['access_token']}",
                "Content-type": "application/json"
            },   
        json=body
    )
    response.raise_for_status()
    df = pd.DataFrame.from_records(response.json()['results'][0]['tables'][0]['rows'])

    return df 

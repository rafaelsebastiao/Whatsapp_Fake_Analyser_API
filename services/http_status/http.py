from fastapi.exceptions import HTTPException

from http import HTTPStatus

def verify_status_http(response):
    if not response.is_success:

        if response.status_code == 401:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail='Unhautorized! Api Key is missing or is incorrect!'
            )
         
        else:
            raise HTTPException(
                status_code=HTTPStatus.BAD_GATEWAY,
                detail=f"Evolution sends {response.status_code} in {response.request.method} {response.request.url}: {response.text} "
            )


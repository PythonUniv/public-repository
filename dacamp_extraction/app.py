from io import StringIO
import uvicorn
from fastapi import FastAPI, Query, status
from fastapi.responses import Response


from extract_code import (get_extracted_page,
                          get_title_from_url,
                          PygmentsStyle)


app = FastAPI()


@app.get('/extract')
def get_blocks(
    url: str,
    style: PygmentsStyle = PygmentsStyle.default,
    max_line_length: int | None = Query(None, min=40, max=140)
) -> Response:
    
    # buffer for saving result
    buffer = StringIO()
    
    # write extraction into buffer
    get_extracted_page(url, file=buffer, style=style, line_length=max_line_length)
    
    # filename of returned file
    filename = get_title_from_url(url)
    
    # return at the beginning of buffer to read all bytes for response
    buffer.seek(0)
    
    return Response(
        content=buffer.getvalue(),
        status_code=status.HTTP_201_CREATED,
        media_type='text/html',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


if __name__ == '__main__':
    uvicorn.run(app)

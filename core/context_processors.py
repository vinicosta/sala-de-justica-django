import hashlib

def gravatar(request):
    if request.user.is_authenticated and request.user.email:
        email = request.user.email.strip().lower().encode()
        gravatar_hash = hashlib.sha256(email).hexdigest()
        gravatar_url = f"https://gravatar.com/avatar/{gravatar_hash}?size=80&d=mp"
    else:
        gravatar_url = ""

    return {
        "gravatar_url": gravatar_url,
        "branding": "Sala de Justiça / App",
    }
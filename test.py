
# A Test outcome of the framework

from anglo import Anglo, Router, render


router = Router()

@router.get("/")
def homepage(request):
    return render("<h1>{{ title }}<h1>", title="Homepage")

@router.get("/about")
def homepage(request):
    return render("<h1>{{ title }}<h1>", title="About")


if __name__ == "__main__":
    app = Anglo(__name__)
    app.useRouter(router)

    app.run("", 8080, server="gunicorn")
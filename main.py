"""FastAPI: sirve la interfaz y genera CV en PDF directamente en memoria."""

from html import escape
from io import BytesIO
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Frame, HRFlowable, Paragraph, Spacer

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="Generador de CV")
PAGE_WIDTH, PAGE_HEIGHT = A4
LEFT_WIDTH = PAGE_WIDTH * 0.65
TOP, BOTTOM = PAGE_HEIGHT - 34, 32

STYLES = {
    "name": ParagraphStyle(
        "name",
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#55555e"),
        spaceAfter=6,
    ),
    "body": ParagraphStyle(
        "body",
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#444444"),
    ),
    "small": ParagraphStyle(
        "small",
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#777777"),
    ),
    "title": ParagraphStyle(
        "title",
        fontName="Helvetica",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#555555"),
        spaceBefore=12,
        spaceAfter=7,
    ),
    "bold": ParagraphStyle(
        "bold",
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#444444"),
    ),
    "right_title": ParagraphStyle(
        "right_title",
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#444444"),
        spaceBefore=5,
        spaceAfter=8,
    ),
    "right_body": ParagraphStyle(
        "right_body",
        fontName="Helvetica",
        fontSize=9,
        leading=14,
        leftIndent=9,
        textColor=colors.HexColor("#333333"),
    ),
    "date": ParagraphStyle(
        "date",
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        alignment=TA_RIGHT,
        textColor=colors.HexColor("#777777"),
    ),
}


def _text(value: object) -> str:
    return escape(str(value if value is not None else "")).replace("\n", "<br/>")


def _debe_incluir(item: object) -> tuple[bool, str]:
    """
    Evalúa si un elemento de lista debe incluirse según el flag 'incluir'.
    Soporta objetos dict con {'texto': '...', 'incluir': True/False} y cadenas simples.
    """
    if isinstance(item, dict):
        incluir = item.get("incluir", True)
        if incluir is False or str(incluir).lower() in ("false", "0", "off"):
            return False, ""
        texto = item.get("texto") or item.get("nombre") or item.get("valor") or ""
        return True, str(texto)
    elif isinstance(item, (str, int, float)):
        texto = str(item).strip()
        return bool(texto), texto
    return False, ""


def _section(story: list, title: str, right: bool = False) -> None:
    if right:
        story.append(
            HRFlowable(
                width="100%",
                thickness=7,
                color=colors.HexColor("#c01b2f"),
                spaceBefore=13,
                spaceAfter=7,
            )
        )
        story.append(Paragraph(title, STYLES["right_title"]))
    else:
        story.append(Paragraph(title.upper(), STYLES["title"]))
        story.append(
            HRFlowable(
                width="100%",
                thickness=0.5,
                color=colors.HexColor("#777777"),
                spaceAfter=8,
            )
        )


def _left_story(data: dict) -> list:
    candidate = data.get("candidato") or {}
    if not isinstance(candidate, dict):
        candidate = {}
    story = [
        Paragraph(_text(candidate.get("nombre", "")), STYLES["name"]),
        Paragraph(
            f'<font color="#3b9eeb">Experiencia:</font> <b>{_text(candidate.get("anos_experiencia", ""))}</b>',
            STYLES["body"],
        ),
        Spacer(1, 11),
    ]
    _section(story, "Experiencia profesional")
    for job in data.get("experiencia_profesional") or []:
        if not isinstance(job, dict):
            continue

        incluir = job.get("incluir", True)
        if incluir is False or str(incluir).lower() in ("false", "0", "off"):
            continue

        story.extend(
            [
                Paragraph(_text(job.get("posicion", "")), STYLES["bold"]),
                Paragraph(
                    f'{_text(job.get("compania", ""))} / {_text(job.get("fecha_inicio", ""))} - {_text(job.get("fecha_fin", ""))}',
                    STYLES["small"],
                ),
                Paragraph(f'{_text(job.get("descripcion", ""))}', STYLES["body"]),
                Spacer(1, 12),
            ]
        )

    # --- COMPLEMENTOS EN EL LADO IZQUIERDO ---
    _section(story, "Complementos")
    for item in data.get("complementos") or []:
        incluir, texto = _debe_incluir(item)
        if incluir and texto:
            story.append(Paragraph(f"• {_text(texto)}", STYLES["body"]))
            story.append(Spacer(1, 5))

    return story


def _right_story(data: dict) -> list:
    story = [Spacer(1, 65)]

    # 1. Habilidades en primer lugar
    _section(story, "Habilidades", right=True)
    for item in data.get("habilidades") or []:
        incluir, texto = _debe_incluir(item)
        if incluir and texto:
            story.append(Paragraph(f"• {_text(texto)}", STYLES["right_body"]))
            story.append(Spacer(1, 5))

    # 2. Educación en el lado derecho
    _section(story, "Educación", right=True)
    for education in data.get("educacion") or []:
        if not isinstance(education, dict):
            continue
        # dates = f'{_text(education.get("fecha_inicio", ""))} - {_text(education.get("fecha_fin", ""))}'
        story.extend(
            [
                # Paragraph(dates, STYLES["date"]),
                Paragraph(_text(education.get("grado", "")), STYLES["body"]),
                Paragraph(_text(education.get("universidad", "")), STYLES["bold"]),
                Spacer(1, 8),
            ]
        )

    # 3. Hard Skills (Experiencia)
    _section(story, "Experiencia", right=True)
    for item in data.get("hard_skills") or []:
        incluir, texto = _debe_incluir(item)
        if incluir and texto:
            story.append(Paragraph(f"• {_text(texto)}", STYLES["right_body"]))
            story.append(Spacer(1, 5))

    # 4. Idiomas
    _section(story, "Idiomas", right=True)
    for value in data.get("idiomas") or []:
        if isinstance(value, (str, int, float)):
            story.append(Paragraph(f"• {_text(value)}", STYLES["right_body"]))
            story.append(Spacer(1, 5))

    return story


def _draw_page(canvas, first_page: bool) -> None:
    canvas.setFillColor(colors.HexColor("#e6e6e6"))
    canvas.rect(LEFT_WIDTH, 0, PAGE_WIDTH - LEFT_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    if first_page:
        logo = BASE_DIR / "Nfq_Logo.png"
        if logo.is_file():
            canvas.drawImage(
                str(logo),
                LEFT_WIDTH + 15,
                PAGE_HEIGHT - 90,
                width=PAGE_WIDTH - LEFT_WIDTH - 30,
                height=55,
                preserveAspectRatio=True,
                anchor="c",
                mask="auto",
            )


def crear_pdf(data: dict) -> bytes:
    """Renderiza el CV sin escribir HTML o PDF en el servidor."""
    from reportlab.pdfgen import canvas as pdf_canvas

    output = BytesIO()
    canvas = pdf_canvas.Canvas(output, pagesize=A4)
    left, right = _left_story(data), _right_story(data)
    first_page = True
    while left or right:
        _draw_page(canvas, first_page)
        left_frame = Frame(
            30,
            BOTTOM,
            LEFT_WIDTH - 60,
            TOP - BOTTOM,
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )
        right_frame = Frame(
            LEFT_WIDTH + 20,
            BOTTOM,
            PAGE_WIDTH - LEFT_WIDTH - 40,
            TOP - BOTTOM,
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )
        remaining = len(left) + len(right)
        left_frame.addFromList(left, canvas)
        right_frame.addFromList(right, canvas)
        if len(left) + len(right) == remaining:
            raise ValueError("El contenido del CV no cabe en la página")
        canvas.showPage()
        first_page = False
    canvas.save()
    return output.getvalue()


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(BASE_DIR / "web" / "index.html", media_type="text/html")


@app.post("/api/generar-pdf", response_class=Response)
def generar_pdf(datos: dict = Body(...)):
    try:
        pdf = crear_pdf(datos)
    except (ValueError, TypeError, AttributeError) as exc:
        raise HTTPException(
            status_code=422, detail="Los datos del CV no tienen el formato esperado"
        ) from exc
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="NFQ_CV.pdf"',
            "Cache-Control": "no-store",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)

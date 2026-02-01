from db import db
from typing import TypedDict

class RefundTaxonomy(TypedDict):
    title: str
    description: str

def get_refund_taxonomy() -> list[RefundTaxonomy]:
    db_refund_taxonomy = db.execute("select reason, description from refund_taxonomy;")
    return [{
        "title": taxonomy[0],
        "description": taxonomy[1]
    } for taxonomy in db_refund_taxonomy]
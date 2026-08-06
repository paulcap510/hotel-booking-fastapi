from database import SessionLocal
from utils.embeddings import get_embedding
import models

db = SessionLocal()

reviews = db.query(models.Review).filter(models.Review.embedding.is_(None)).all()

print(f"Found {len(reviews)} reviews without embeddings")

for review in reviews:
    vector = get_embedding(review.review_description)
    review.embedding = vector
    print(f"Embedded review {review.id}: {review.review_description[:50]}...")

db.commit()
db.close()
print("Done.")

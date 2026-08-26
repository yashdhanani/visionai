#!/usr/bin/env python3
"""Seed database with demo data for development."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "api"))

from app.config.settings import settings
from app.db.session import Base, SessionLocal, engine
from app.models.db_models import MLModel, ModelStatus, User, UserRole
from app.services.auth_service import create_user, hash_password
from app.services.email_service import send_reset_email


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        admin_email = os.getenv("ADMIN_EMAIL", "admin@visionai.local")
        admin_pass = os.getenv("ADMIN_PASSWORD", "Admin123!")

        if not db.query(User).filter(User.email == admin_email).first():
            user = User(name="Admin", email=admin_email, password_hash=hash_password(admin_pass), role=UserRole.ADMIN, email_verified=True)
            db.add(user)
            db.flush()
            print(f"Created admin: {admin_email} / {admin_pass}")
        else:
            print("Admin already exists")

        demo_email = "demo@visionai.local"
        demo_pass = "Demo123!"
        if not db.query(User).filter(User.email == demo_email).first():
            user = User(name="Demo User", email=demo_email, password_hash=hash_password(demo_pass), role=UserRole.USER, email_verified=True)
            db.add(user)
            db.flush()
            print(f"Created demo: {demo_email} / {demo_pass}")

        models_data = [
            ("YOLOv8n (COCO)", "yolov8n.pt", True, 80, 150.0),
            ("YOLOv8s (COCO)", "yolov8s.pt", False, 80, 80.0),
            ("YOLOv8m (COCO)", "yolov8m.pt", False, 80, 40.0),
        ]
        for name, path, active, classes, fps in models_data:
            if not db.query(MLModel).filter(MLModel.name == name).first():
                model = MLModel(
                    name=name,
                    version="8.0",
                    framework="ultralytics-yolo",
                    path=path,
                    status=ModelStatus.ACTIVE if active else ModelStatus.AVAILABLE,
                    classes_count=classes,
                    inference_speed_fps=fps,
                )
                db.add(model)

        db.commit()
        print("Seed completed")
    finally:
        db.close()


if __name__ == "__main__":
    main()
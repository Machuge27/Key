from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image, ImageDraw
from django.conf import settings
import os

class User(AbstractUser):
    is_student = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_security = models.BooleanField(default=False)
    # status = models.CharField(max_length=20, default='active', 
    #                          choices=[('active', 'Active'), ('deactivated', 'Deactivated'), ('lost', 'Lost'), ('expired', 'Expired')])
    
    def __str__(self):
        return self.username
    


class Student(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile', null=True, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    admission_number = models.CharField(max_length=20, unique=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    status = models.CharField(max_length=20, default='active', 
                             choices=[('active', 'Active'), ('deactivated', 'Deactivated'), ('lost', 'Lost'), ('expired', 'Expired')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.admission_number})"
    
    def save(self, *args, **kwargs):
        # Generate QR code on first save
        if not self.qr_code:
            qr_image = self.generate_qr_code()
            
            # Save the QR code image
            qr_filename = f"qr_{self.admission_number}.png"
            temp_stream = BytesIO()
            qr_image.save(temp_stream, format='PNG')
            temp_stream.seek(0)
            
            # Save to model field
            self.qr_code.save(qr_filename, File(temp_stream), save=False)
        
        super().save(*args, **kwargs)
    
    def generate_qr_code(self):
        # Data to encode in QR code - using the UUID as unique identifier
        qr_data = str(self.id)
        
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Create an image from the QR Code
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Create a canvas with padding
        canvas = Image.new('RGB', (img.pixel_size + 20, img.pixel_size + 50), 'white')
        
        # Add QR code to canvas
        canvas.paste(img, (10, 10))
        
        # Add text with student details
        draw = ImageDraw.Draw(canvas)
        draw.text((10, img.pixel_size + 15), f"Name: {self.name}", fill='black')
        draw.text((10, img.pixel_size + 30), f"ID: {self.admission_number}", fill='black')
        
        return canvas
    
    
    def report_lost(self):
        """Mark the student ID as lost"""
        self.status = 'lost'
        self.save()
        return True
    def deactivate(self):
        """Mark the student ID as deactivated"""
        self.status = 'deactivated'
        self.save()
        return True
    def recover(self):
        """Mark the student ID as active"""
        self.status = 'active'
        self.save()
        return True
    def expire(self):
        """Mark the student ID as expired"""
        self.status = 'expired'
        self.save()
        return True


class EntryLog(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='entries')
    timestamp = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=100, default='Main Gate')
    successful = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.student.name} entered at {self.timestamp}"


class LostCardScan(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='lost_scans')
    timestamp = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=100)
    
    def __str__(self):
        return f"Lost card for {self.student.name} scanned at {self.timestamp}"

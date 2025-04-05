import qrcode
from PIL import Image
import os

def generate_qr_code(data, filename="qr_code.png", box_size=10, border=4, fill_color="black", back_color="white"):
    """
    Generate a QR code from input data and save it as an image file.
    
    Parameters:
    data (str): The data to encode in the QR code
    filename (str): The filename to save the QR code image as
    box_size (int): Size of each box in the QR code (pixels)
    border (int): Border size in boxes
    fill_color (str): Color of the QR code modules (boxes)
    back_color (str): Background color
    
    Returns:
    str: Path to the saved QR code image
    """
    # Create QR code instance
    qr = qrcode.QRCode(
        version=None,  # Auto-determine version
        error_correction=qrcode.constants.ERROR_CORRECT_M,  # Medium error correction
        box_size=box_size,
        border=border
    )
    
    # Add data to QR code
    qr.add_data(data)
    qr.make(fit=True)
    
    # Create an image from the QR code
    img = qr.make_image(fill_color=fill_color, back_color=back_color)
    
    # Save the image
    img.save(filename)
    
    return os.path.abspath(filename)

if __name__ == "__main__":
    # Example usage
    student_id = "STU12345"
    student_name = "John Doe"
    
    # Create data to encode (could be a simple string or formatted data)
    data = f"ID:{student_id}|NAME:{student_name}"
    
    # Generate QR code
    qr_path = generate_qr_code(
        data=data,
        filename=f"qrs/student_{student_id}_qr.png",
        box_size=10,
        border=4
    )
    
    print(f"QR code generated and saved at: {qr_path}")
    print(f"Encoded data: {data}")
    
    
# pip install qrcode pillow pyzbar opencv-python numpy    
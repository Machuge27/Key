from pyzbar.pyzbar import decode
from PIL import Image
import cv2
import numpy as np

def decode_qr_code_from_image(image_path):
    """
    Decode QR code from an image file.
    
    Parameters:
    image_path (str): Path to the image file containing the QR code
    
    Returns:
    str: Decoded data from the QR code
    """
    # Open the image
    image = Image.open(image_path)
    
    # Decode the QR code
    decoded_objects = decode(image)
    
    # Extract results
    if decoded_objects:
        for obj in decoded_objects:
            # Convert bytes to string if necessary
            data = obj.data.decode('utf-8')
            return data
    else:
        return "No QR code found in the image"

def decode_qr_code_from_camera():
    """
    Decode QR code from camera feed in real-time.
    Press 'q' to quit.
    
    Returns:
    str: Decoded data from the QR code
    """
    # Initialize camera
    cap = cv2.VideoCapture(0)
    
    print("Camera started. Show QR code to scan. Press 'q' to quit.")
    
    while True:
        # Read frame from camera
        ret, frame = cap.read()
        
        if not ret:
            print("Failed to grab frame")
            break
            
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Decode QR code
        decoded_objects = decode(gray)
        
        # Process results
        for obj in decoded_objects:
            # Get the data
            data = obj.data.decode('utf-8')
            
            # Draw rectangle around QR code
            points = obj.polygon
            if len(points) > 4:
                hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
                points = hull
            
            num_points = len(points)
            for i in range(num_points):
                cv2.line(frame, 
                         (int(points[i][0]), int(points[i][1])),
                         (int(points[(i+1) % num_points][0]), int(points[(i+1) % num_points][1])),
                         (0, 255, 0), 3)
            
            # Display data
            cv2.putText(frame, data, (obj.rect[0], obj.rect[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Show success message
            print(f"Decoded Data: {data}")
        
        # Display the frame
        cv2.imshow('QR Code Scanner', frame)
        
        # Check for quit command
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Release resources
    cap.release()
    cv2.destroyAllWindows()
    
    return "Scanner closed"

if __name__ == "__main__":
    # Example usage - decode from image file
    image_path = "qrs/qr_E3-2922-2022.png"  # Replace with your QR code image path
    
    try:
        result = decode_qr_code_from_image(image_path)
        print(f"Decoded from image: {result}")
        # print(f"Student ID: {result.split('|')[0][3:]}")
        # print(f"Name: {result.split('|')[1][5:]}")
    except FileNotFoundError:
        print(f"Image file not found: {image_path}")
    
    # Uncomment to use camera scanner
    # result = decode_qr_code_from_camera()
    # print(result)
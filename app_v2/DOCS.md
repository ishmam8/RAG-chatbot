# frontend

## Conceptual React Native Post Request
### /upload
const handleFileUpload = async () => {
  try {
    // 1. Select the file
    const res = await DocumentPicker.pick({
      type: [DocumentPicker.types.pdf], // Or allow all types and check later
    });
    // res will be an array, pick the first one for single file upload
    const selectedFile = res[0];

    // 2. Create FormData
    const formData = new FormData();
    formData.append('file', {
      uri: selectedFile.uri,
      type: selectedFile.type, // e.g., 'application/pdf'
      name: selectedFile.name, // e.g., 'mydocument.pdf'
    });

    // 3. Make the POST request
    const token = "YOUR_AUTH_TOKEN_HERE"; // Get this from your auth flow
    const response = await fetch('YOUR_FASTAPI_ENDPOINT/documents/upload', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        // 'Content-Type': 'multipart/form-data' // Usually set automatically by fetch for FormData
      },
      body: formData,
    });

    const responseData = await response.json();

    if (response.ok) {
      console.log('Upload successful:', responseData);
      // Handle successful upload
    } else {
      console.error('Upload failed:', responseData);
      // Handle error
    }
  } catch (err) {
    if (DocumentPicker.isCancel(err)) {
      // User cancelled the picker
    } else {
      console.error('Error during file upload:', err);
    }
  }
};
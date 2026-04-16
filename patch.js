            // Handle form submission
            chatForm.addEventListener('submit', async function(e) {
                e.preventDefault();

                // Get message from input or transcribed text
                const message = messageInput.value.trim();
                if (!message) return;

                // --- ADDED: Automatically stop any playing audio immediately when submitting ---
                if (currentAudio) {
                    currentAudio.pause();
                    currentAudio.currentTime = 0;
                    URL.revokeObjectURL(currentAudio.src);
                    currentAudio = null;

                    // Reset all play buttons in the UI
                    document.querySelectorAll('.play-tts-btn').forEach(btn => {
                        if (btn.classList.contains('btn-primary')) {
                            btn.innerHTML = '<i class="fas fa-play"></i> ' + translations[currentLanguage].playVoice;
                            btn.classList.remove('btn-primary');
                            btn.classList.add('btn-outline-primary');
                        }
                    });

                    document.querySelectorAll('.stop-tts-btn').forEach(btn => {
                        btn.classList.add('d-none');
                    });
                }
                // --------------------------------------------------------------------------------

                // Add user message to chat
                const userMessageElement = document.createElement('div');
                userMessageElement.className = 'message user-message';

                // Create message content
                let messageContent = `<p>${message}</p>`;

                userMessageElement.innerHTML = messageContent;
                chatBody.appendChild(userMessageElement);

                // Add thinking indicator
                const thinkingElement = document.createElement('div');
                thinkingElement.className = 'message assistant-message thinking';
                thinkingElement.innerHTML = `
                    <div class="typing-indicator">
                        <span></span><span></span><span></span>
                    </div>
                `;
                chatBody.appendChild(thinkingElement);

                // Scroll to bottom
                chatBody.scrollTop = chatBody.scrollHeight;

                // Clear input
                messageInput.value = '';
                messageInput.style.height = 'auto';

                try {
                    let response;

                    // Send to backend using the /chat endpoint
                    response = await fetch('/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            query: message,
                            language: currentLanguage,
                            preferred_agent: currentSelectedAgent
                        })
                    });

                    const data = await response.json();

                    // Remove thinking indicator
                    chatBody.removeChild(thinkingElement);

                    if (response.ok) {
                        appendAssistantResponse(data);
                    } else {
                        // Error handling
                        const errorElement = document.createElement('div');
                        errorElement.className = 'message assistant-message bg-light border border-danger';
                        errorElement.innerHTML = `
                            <div class="agent-tag text-danger">System</div>
                            <p class="text-danger mb-2">${translations[currentLanguage].sysError}</p>
                            <div class="bg-white p-2 rounded small text-danger font-monospace" style="white-space: pre-wrap; overflow-x: auto;">${data.detail || data.response || 'Unknown error'}</div>
                        `;
                        chatBody.appendChild(errorElement);
                    }
                } catch (error) {
                    chatBody.removeChild(thinkingElement);

                    const errorElement = document.createElement('div');
                    errorElement.className = 'message assistant-message bg-light border border-danger';
                    errorElement.innerHTML = `
                        <div class="agent-tag text-danger">System</div>
                        <p class="text-danger mb-2">${translations[currentLanguage].sysError}</p>
                        <div class="bg-white p-2 rounded small text-danger font-monospace" style="white-space: pre-wrap; overflow-x: auto;">${error.message || error}</div>
                    `;
                    chatBody.appendChild(errorElement);
                }

                // Scroll to bottom
                chatBody.scrollTop = chatBody.scrollHeight;
            });

            // Handle CV Form submission
            cvForm.addEventListener('submit', async function(e) {
                e.preventDefault();
                
                if (!cvImageUpload.files.length) return;
                
                // --- ADDED: Automatically stop any playing audio immediately when submitting ---
                if (currentAudio) {
                    currentAudio.pause();
                    currentAudio.currentTime = 0;
                    URL.revokeObjectURL(currentAudio.src);
                    currentAudio = null;
                    
                    // Reset all play buttons in the UI
                    document.querySelectorAll('.play-tts-btn').forEach(btn => {
                        if (btn.classList.contains('btn-primary')) {
                            btn.innerHTML = '<i class="fas fa-play"></i> ' + translations[currentLanguage].playVoice;
                            btn.classList.remove('btn-primary');
                            btn.classList.add('btn-outline-primary');
                        }
                    });
                    
                    document.querySelectorAll('.stop-tts-btn').forEach(btn => {
                        btn.classList.add('d-none');
                    });
                }
                // --------------------------------------------------------------------------------

                // Store image data if available
                let imageDataUrl = cvPreviewImage.src;
                const selectedTask = document.querySelector('input[name="cvTask"]:checked').value;
                const taskLabel = selectedTask === 'STROKE' ? 'Stroke Detection' : 'Brain Tumor Detection';
                
                // Add user message to chat
                const userMessageElement = document.createElement('div');
                userMessageElement.className = 'message user-message';
                
                let messageContent = `<p><strong>[${translations[currentLanguage].cvTab}]</strong> ${taskLabel}</p>`;
                messageContent += `
                    <div class="mt-2">
                        <img src="${imageDataUrl}" alt="Uploaded image" class="img-fluid rounded" style="max-height: 200px;">
                    </div>
                `;
                
                userMessageElement.innerHTML = messageContent;
                chatBody.appendChild(userMessageElement);
                
                // Add thinking indicator
                const thinkingElement = document.createElement('div');
                thinkingElement.className = 'message assistant-message thinking';
                thinkingElement.innerHTML = `
                    <div class="typing-indicator">
                        <span></span><span></span><span></span>
                    </div>
                `;
                chatBody.appendChild(thinkingElement);
                
                // Scroll to bottom
                chatBody.scrollTop = chatBody.scrollHeight;
                
                // Clear input
                cvRemoveImageBtn.click();
                
                try {
                    const formData = new FormData();
                    formData.append('image', cvImageUpload.files[0]);
                    formData.append('task', selectedTask);
                    formData.append('language', currentLanguage);
                    
                    const response = await fetch('/cv_upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    // Remove thinking indicator
                    chatBody.removeChild(thinkingElement);
                    
                    if (response.ok) {
                        appendAssistantResponse(data);
                    } else {
                        // Error handling
                        const errorElement = document.createElement('div');
                        errorElement.className = 'message assistant-message bg-light border border-danger';
                        errorElement.innerHTML = `
                            <div class="agent-tag text-danger">System</div>
                            <p class="text-danger mb-2">${translations[currentLanguage].sysError}</p>
                            <div class="bg-white p-2 rounded small text-danger font-monospace" style="white-space: pre-wrap; overflow-x: auto;">${data.detail || data.response || 'Unknown error'}</div>
                        `;
                        chatBody.appendChild(errorElement);
                    }
                } catch (error) {
                    chatBody.removeChild(thinkingElement);
                    
                    const errorElement = document.createElement('div');
                    errorElement.className = 'message assistant-message bg-light border border-danger';
                    errorElement.innerHTML = `
                        <div class="agent-tag text-danger">System</div>
                        <p class="text-danger mb-2">${translations[currentLanguage].sysError}</p>
                        <div class="bg-white p-2 rounded small text-danger font-monospace" style="white-space: pre-wrap; overflow-x: auto;">${error.message || error}</div>
                    `;
                    chatBody.appendChild(errorElement);
                }
                
                // Scroll to bottom
                chatBody.scrollTop = chatBody.scrollHeight;
            });

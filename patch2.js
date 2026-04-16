            function appendAssistantResponse(data, uploadedImageDataUrl = null) {
                const assistantMessageElement = document.createElement('div');
                assistantMessageElement.className = 'message assistant-message';

                const cleanText = removeMarkdown(data.response);

                let assistantHtml = `
                    <div class="agent-tag">${data.agent === "HUMAN_VALIDATED" ? translations[currentLanguage].humanVal : data.agent}</div>
                    <div>${marked.parse(data.response)}</div>
                    <div class="audio-controls mt-2 d-flex align-items-center">
                        <button class="btn btn-sm btn-outline-primary play-tts-btn">
                            <i class="fas fa-play"></i> ${translations[currentLanguage].playVoice}
                        </button>
                        <button class="btn btn-sm btn-outline-danger stop-tts-btn d-none ms-2" title="Stop Audio">
                            <i class="fas fa-stop"></i>
                        </button>
                    </div>
                `;

                if (data.agent.includes("HUMAN_VALIDATION")) {
                    assistantHtml += `
                        <div class="mt-3 p-3 border rounded bg-light">
                            <p><strong>${translations[currentLanguage].humanValReq}</strong></p>
                            <button class="btn btn-success btn-sm validate-btn" data-validation="yes">${translations[currentLanguage].valYes}</button>
                            <button class="btn btn-danger btn-sm validate-btn" data-validation="no">${translations[currentLanguage].valNo}</button>
                            <textarea class="form-control mt-2 validation-comments" rows="2" placeholder="${translations[currentLanguage].valComments}"></textarea>
                        </div>
                    `;
                }

                if (data.result_image) {
                    if (data.agent === "SKIN_LESION_AGENT, HUMAN_VALIDATION" && uploadedImageDataUrl) {
                        assistantHtml += `
                            <div class="image-side-by-side">
                                <div class="image-container">
                                    <img src="${uploadedImageDataUrl}" alt="Original image" class="img-fluid rounded">
                                    <div class="image-caption">${translations[currentLanguage].origImage}</div>
                                </div>
                                <div class="image-container">
                                    <img src="${data.result_image}" alt="Segmented image" class="img-fluid rounded">
                                    <div class="image-caption">${translations[currentLanguage].segResult}</div>
                                </div>
                            </div>
                        `;
                    } else {
                        assistantHtml += `
                            <div class="mt-3">
                                <img src="${data.result_image}" alt="Result image" class="result-image">
                            </div>
                        `;
                    }
                }

                assistantMessageElement.innerHTML = assistantHtml;
                chatBody.appendChild(assistantMessageElement);

                if (data.agent.includes("HUMAN_VALIDATION")) {
                    document.querySelectorAll('.validate-btn').forEach(button => {
                        button.addEventListener('click', async function () {
                            const validation = this.getAttribute('data-validation');
                            const comments = this.closest('.p-3').querySelector('.validation-comments').value;
                            await sendValidation(validation, comments);
                        });
                    });
                }

                const playButton = assistantMessageElement.querySelector('.play-tts-btn');
                const stopButton = assistantMessageElement.querySelector('.stop-tts-btn');

                function resetAllAudioUI() {
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

                stopButton.addEventListener('click', function() {
                    if (currentAudio) {
                        currentAudio.pause();
                        currentAudio.currentTime = 0;
                        URL.revokeObjectURL(currentAudio.src);
                        currentAudio = null;
                    }
                    resetAllAudioUI();
                });

                playButton.addEventListener('click', async function () {
                    const textForSpeech = cleanText.length > 1000 ? cleanText.substring(0, 1000) + "..." : cleanText;
                    this.disabled = true;
                    this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';

                    try {
                        const audioUrl = await generateSpeech(textForSpeech);

                        if (currentAudio) {
                            currentAudio.pause();
                            currentAudio.currentTime = 0;
                            URL.revokeObjectURL(currentAudio.src);
                            currentAudio = null;
                        }

                        resetAllAudioUI();

                        currentAudio = new Audio(audioUrl);

                        currentAudio.onplay = () => {
                            this.innerHTML = '<i class="fas fa-pause"></i> Pause';
                            this.classList.remove('btn-outline-primary');
                            this.classList.add('btn-primary');
                            stopButton.classList.remove('d-none');
                            this.disabled = false;
                        };

                        currentAudio.onpause = () => {
                            this.innerHTML = '<i class="fas fa-play"></i> ' + translations[currentLanguage].playVoice;
                            this.classList.remove('btn-primary');
                            this.classList.add('btn-outline-primary');
                            stopButton.classList.add('d-none');
                        };

                        currentAudio.onended = () => {
                            this.innerHTML = '<i class="fas fa-play"></i> ' + translations[currentLanguage].playVoice;
                            this.classList.remove('btn-primary');
                            this.classList.add('btn-outline-primary');
                            stopButton.classList.add('d-none');
                        };

                        currentAudio.play().catch(e => {
                            console.error('Playback failed:', e);
                            this.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error';
                            this.classList.remove('btn-primary');
                            this.classList.add('btn-outline-danger');
                            this.disabled = false;
                        });
                    } catch (e) {
                        console.error('Speech generation failed:', e);
                        this.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error';
                        this.disabled = false;
                    }
                });
            }

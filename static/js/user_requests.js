(function () {
    const ready = (callback) => {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', callback);
        } else {
            callback();
        }
    };

    const buildUrl = (template, id) => template.replace(/0(?!.*0)/, String(id));

    const getCsrfToken = () => {
        const cookieValue = document.cookie
            .split('; ')
            .find((row) => row.startsWith('csrftoken='));
        if (!cookieValue) {
            return '';
        }
        return decodeURIComponent(cookieValue.split('=')[1]);
    };

    const truncate = (text, maxLength) => {
        if (!text) {
            return '';
        }
        if (text.length <= maxLength) {
            return text;
        }
        return `${text.slice(0, maxLength - 1).trim()}…`;
    };

    ready(() => {
        const section = document.querySelector('[data-requests-section]');
        const modal = document.querySelector('[data-user-request-modal]');
        if (!section || !modal) {
            return;
        }

        const track = section.querySelector('[data-carousel-track]');
        const prevButton = section.querySelector('[data-carousel-prev]');
        const nextButton = section.querySelector('[data-carousel-next]');
        const detailTemplate = modal.dataset.detailTemplate || '';
        const updateTemplate = modal.dataset.updateTemplate || '';
        const deleteTemplate = modal.dataset.deleteTemplate || '';
        const statusMap = JSON.parse(modal.dataset.statusMap || '{}');
        const detailErrorMessage = modal.dataset.detailError || 'Unable to load request.';
        const updateErrorMessage = modal.dataset.updateError || 'Could not save changes.';
        const deleteConfirmMessage = modal.dataset.deleteConfirm || 'Are you sure?';
        const language = modal.dataset.language || 'pl';

        const form = modal.querySelector('[data-user-request-form]');
        const errorBox = modal.querySelector('[data-user-request-error]');
        const statusBadge = modal.querySelector('[data-user-request-status-badge]');
        const titleElement = modal.querySelector('[data-user-request-title]');
        const createdElement = modal.querySelector('[data-user-request-created]');
        const finalChangesElement = modal.querySelector('[data-user-request-final-changes]');
        const finalResponseElement = modal.querySelector('[data-user-request-final-response]');
        const closeElements = Array.from(modal.querySelectorAll('[data-user-request-close]'));
        const deleteButton = modal.querySelector('[data-user-request-delete]');
        const attachmentsList = modal.querySelector('[data-user-request-attachments]');
        const attachmentsEmptyMessage = attachmentsList ? attachmentsList.dataset.empty || '' : '';
        const attachmentsField = form ? form.querySelector('input[name="attachments"]') : null;

        let cards = track ? Array.from(track.querySelectorAll('[data-request-card]')) : [];
        let currentIndex = 0;
        let currentCard = null;
        let currentId = null;
        let isBusy = false;

        const emptyMessage = section.dataset.emptyMessage || '';
        const emptyActionLabel = section.dataset.emptyActionLabel || '';
        const emptyActionUrl = section.dataset.emptyActionUrl || '#';

        const updateButtons = () => {
            if (!cards.length) {
                if (prevButton) {
                    prevButton.disabled = true;
                }
                if (nextButton) {
                    nextButton.disabled = true;
                }
                return;
            }
            if (prevButton) {
                prevButton.disabled = currentIndex <= 0;
            }
            if (nextButton) {
                nextButton.disabled = currentIndex >= cards.length - 1;
            }
        };

        const scrollToIndex = (index) => {
            if (!track) {
                return;
            }
            const card = cards[index];
            if (!card) {
                return;
            }
            const offset = card.offsetLeft - track.offsetLeft;
            track.scrollTo({ left: offset, behavior: 'smooth' });
            currentIndex = index;
            updateButtons();
        };

        const refreshCards = () => {
            cards = track ? Array.from(track.querySelectorAll('[data-request-card]')) : [];
            if (!cards.length) {
                currentIndex = 0;
            } else if (currentIndex >= cards.length) {
                currentIndex = cards.length - 1;
            }
            updateButtons();
        };

        const showError = (message) => {
            if (!errorBox) {
                return;
            }
            errorBox.textContent = message;
            errorBox.hidden = !message;
        };

        const setStatusBadge = (target, statusKey, fallbackLabel) => {
            if (!target) {
                return;
            }
            const info = statusMap[statusKey] || {};
            const label = info.label || fallbackLabel || statusKey || '';
            const badgeClass = info.badge || 'badge--info';
            target.className = `badge ${badgeClass}`.trim();
            target.textContent = label;
        };

        const setFinalText = (element, value) => {
            if (!element) {
                return;
            }
            const content = (value || '').trim();
            if (content) {
                element.textContent = content;
            } else {
                element.textContent = element.dataset.empty || '';
            }
        };

        const renderAttachments = (items) => {
            if (!attachmentsList) {
                return;
            }
            attachmentsList.innerHTML = '';
            if (!items || !items.length) {
                if (attachmentsEmptyMessage) {
                    const emptyItem = document.createElement('li');
                    emptyItem.className = 'attachment-list__empty';
                    emptyItem.textContent = attachmentsEmptyMessage;
                    attachmentsList.appendChild(emptyItem);
                }
                return;
            }
            items.forEach((item) => {
                const listItem = document.createElement('li');
                listItem.className = 'attachment-list__item';
                const link = document.createElement('a');
                link.href = item.url || '#';
                link.target = '_blank';
                link.rel = 'noopener';
                link.textContent = item.name || 'attachment';
                listItem.appendChild(link);
                if (item.size) {
                    const meta = document.createElement('span');
                    meta.className = 'attachment-list__meta';
                    const sizeKb = (Number(item.size) / 1024).toFixed(1);
                    meta.textContent = `${sizeKb} KB`;
                    listItem.appendChild(meta);
                }
                attachmentsList.appendChild(listItem);
            });
        };

        const populateForm = (data) => {
            if (!form) {
                return;
            }
            form.reset();
            Object.entries(data).forEach(([key, value]) => {
                const field = form.elements.namedItem(key);
                if (!field) {
                    return;
                }
                if (field instanceof HTMLInputElement || field instanceof HTMLTextAreaElement) {
                    field.value = value ?? '';
                } else if (field instanceof HTMLSelectElement) {
                    field.value = value ?? '';
                }
            });
            setFinalText(finalChangesElement, data.final_changes);
            setFinalText(finalResponseElement, data.final_response);
            renderAttachments(data.attachments || []);
        };

        const setModalHeader = (data) => {
            if (titleElement) {
                const prefix = language === 'pl' ? 'Zgłoszenie #' : 'Request #';
                titleElement.textContent = data.id ? `${prefix}${data.id}` : prefix;
            }
            if (createdElement) {
                const label = language === 'pl' ? 'Utworzone:' : 'Created:';
                createdElement.textContent = data.created_at ? `${label} ${data.created_at}` : '';
            }
            setStatusBadge(statusBadge, data.status, data.status_label);
        };

        const toggleModal = (shouldOpen) => {
            if (shouldOpen) {
                modal.classList.add('is-visible');
                modal.setAttribute('aria-hidden', 'false');
                document.body.classList.add('has-open-modal');
                const firstField = form ? form.querySelector('input, textarea, select') : null;
                if (firstField instanceof HTMLElement) {
                    firstField.focus({ preventScroll: true });
                }
            } else {
                modal.classList.remove('is-visible');
                modal.setAttribute('aria-hidden', 'true');
                document.body.classList.remove('has-open-modal');
                currentCard = null;
                currentId = null;
                showError('');
                renderAttachments([]);
                if (attachmentsField) {
                    attachmentsField.value = '';
                }
            }
        };

        const openEmptyState = () => {
            if (section.querySelector('.requests-empty')) {
                return;
            }
            const empty = document.createElement('div');
            empty.className = 'requests-empty';
            const message = document.createElement('p');
            message.textContent = emptyMessage;
            empty.appendChild(message);
            const action = document.createElement('a');
            action.className = 'button button--primary';
            action.href = emptyActionUrl;
            action.textContent = emptyActionLabel;
            empty.appendChild(action);
            section.appendChild(empty);
            const carousel = section.querySelector('[data-request-carousel]');
            if (carousel) {
                carousel.remove();
            }
        };

        const updateCardDisplay = (card, data) => {
            if (!card) {
                return;
            }
            const statusElement = card.querySelector('[data-card-status]');
            setStatusBadge(statusElement, data.status, data.status_label);
            const meta = card.querySelector('.request-card__meta');
            if (meta) {
                meta.textContent = `${data.created_at} · ${data.company_label}`;
            }
            const message = card.querySelector('.request-card__message');
            if (message) {
                message.textContent = truncate(data.message || '', 140);
            }
        };

        const fetchDetails = (card) => {
            if (!card || isBusy) {
                return;
            }
            const id = card.dataset.requestId;
            if (!id) {
                return;
            }
            const url = buildUrl(detailTemplate, id);
            if (!url) {
                return;
            }
            isBusy = true;
            showError('');
            fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            })
                .then((response) => {
                    if (!response.ok) {
                        throw new Error(String(response.status));
                    }
                    return response.json();
                })
                .then((data) => {
                    currentCard = card;
                    currentId = data.id;
                    populateForm(data);
                    setModalHeader(data);
                    toggleModal(true);
                })
                .catch(() => {
                    alert(detailErrorMessage);
                })
                .finally(() => {
                    isBusy = false;
                });
        };

        const submitUpdate = () => {
            if (!form || !currentId) {
                return;
            }
            const url = buildUrl(updateTemplate, currentId);
            if (!url) {
                return;
            }
            const formData = new FormData(form);
            const csrfToken = formData.get('csrfmiddlewaretoken') || getCsrfToken();
            isBusy = true;
            showError('');
            fetch(url, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken,
                },
                body: formData,
            })
                .then((response) => {
                    if (response.ok) {
                        return response.json();
                    }
                    return response.json().then((data) => {
                        throw data;
                    });
                })
                .then((data) => {
                    if (currentCard) {
                        updateCardDisplay(currentCard, data);
                    }
                    populateForm(data);
                    setModalHeader(data);
                    showError('');
                })
                .catch((error) => {
                    if (error && error.errors) {
                        const messages = Object.values(error.errors)
                            .flat()
                            .join(' ');
                        showError(messages || updateErrorMessage);
                    } else {
                        showError(updateErrorMessage);
                    }
                })
                .finally(() => {
                    isBusy = false;
                });
        };

        const deleteRequest = () => {
            if (!currentId || !currentCard) {
                return;
            }
            if (!window.confirm(deleteConfirmMessage)) {
                return;
            }
            const url = buildUrl(deleteTemplate, currentId);
            if (!url) {
                return;
            }
            const csrfToken = getCsrfToken();
            isBusy = true;
            fetch(url, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken,
                },
            })
                .then((response) => {
                    if (!response.ok) {
                        throw new Error(String(response.status));
                    }
                    return response.json();
                })
                .then(() => {
                    currentCard.remove();
                    toggleModal(false);
                    refreshCards();
                    if (!cards.length) {
                        openEmptyState();
                    } else if (track) {
                        cards = Array.from(track.querySelectorAll('[data-request-card]'));
                        const targetIndex = Math.min(currentIndex, cards.length - 1);
                        scrollToIndex(targetIndex);
                    }
                })
                .catch(() => {
                    alert(updateErrorMessage);
                })
                .finally(() => {
                    isBusy = false;
                });
        };

        const attachCardHandlers = () => {
            cards.forEach((card, index) => {
                card.addEventListener('click', () => {
                    currentIndex = index;
                    updateButtons();
                    fetchDetails(card);
                });
                card.addEventListener('keydown', (event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        currentIndex = index;
                        updateButtons();
                        fetchDetails(card);
                    }
                });
            });
        };

        attachCardHandlers();
        updateButtons();

        if (prevButton) {
            prevButton.addEventListener('click', () => {
                if (currentIndex > 0) {
                    scrollToIndex(currentIndex - 1);
                }
            });
        }

        if (nextButton) {
            nextButton.addEventListener('click', () => {
                if (currentIndex < cards.length - 1) {
                    scrollToIndex(currentIndex + 1);
                }
            });
        }

        if (form) {
            form.addEventListener('submit', (event) => {
                event.preventDefault();
                submitUpdate();
            });
        }

        if (deleteButton) {
            deleteButton.addEventListener('click', (event) => {
                event.preventDefault();
                deleteRequest();
            });
        }

        closeElements.forEach((element) => {
            element.addEventListener('click', () => toggleModal(false));
        });

        const modalBackdrop = modal.querySelector('.modal__backdrop');
        if (modalBackdrop) {
            modalBackdrop.addEventListener('click', () => toggleModal(false));
        }

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && modal.classList.contains('is-visible')) {
                toggleModal(false);
            }
        });
    });
})();

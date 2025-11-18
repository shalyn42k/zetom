(function () {
    const ready = (callback) => {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', callback);
        } else {
            callback();
        }
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
        if (!section || !modal || !window.ZetomRequestModal) {
            return;
        }

        const { RequestModalController } = window.ZetomRequestModal;

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
        const lockedMessage = modal.dataset.lockedMessage || updateErrorMessage;

        const emptyMessage = section.dataset.emptyMessage || '';
        const emptyActionLabel = section.dataset.emptyActionLabel || '';
        const emptyActionUrl = section.dataset.emptyActionUrl || '#';

        const statusLookup = (status) => statusMap[status] || {};

        let cards = track ? Array.from(track.querySelectorAll('[data-request-card]')) : [];
        let currentIndex = 0;
        let currentCard = null;

        const setStatusBadge = (target, statusKey, fallbackLabel) => {
            if (!target) {
                return;
            }
            const info = statusLookup(statusKey);
            const label = info.label || fallbackLabel || statusKey || '';
            const badgeClass = info.badge || 'badge--info';
            target.className = `badge ${badgeClass}`.trim();
            target.textContent = label;
        };

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
                const extra = data.company_name ? ` — ${data.company_name}` : '';
                meta.textContent = `${data.created_at} · ${data.company_label}${extra}`;
            }
            const message = card.querySelector('.request-card__message');
            if (message) {
                message.textContent = truncate(data.message || '', 140);
            }
        };

        const controller = new RequestModalController(modal, {
            statusMap,
            detailTemplate,
            updateTemplate,
            deleteTemplate,
            detailErrorMessage,
            updateErrorMessage,
            deleteConfirmMessage,
            lockedMessage,
            language,
            onAfterUpdate(data) {
                if (currentCard) {
                    updateCardDisplay(currentCard, data);
                }
            },
            onAfterDelete() {
                if (!currentCard) {
                    refreshCards();
                    return;
                }
                const removedCard = currentCard;
                const removedIndex = cards.indexOf(removedCard);
                removedCard.remove();
                currentCard = null;
                refreshCards();
                if (!cards.length) {
                    openEmptyState();
                } else if (track) {
                    const targetIndex = Math.min(removedIndex, cards.length - 1);
                    scrollToIndex(targetIndex);
                }
            },
            onClose() {
                currentCard = null;
            },
        });

        const openCard = (card, index) => {
            const requestId = card.dataset.requestId;
            if (!requestId) {
                return;
            }
            currentCard = card;
            currentIndex = index;
            updateButtons();
            controller.openForId(requestId).catch(() => {
                currentCard = null;
            });
        };

        const attachCardHandlers = () => {
            cards.forEach((card, index) => {
                card.addEventListener('click', () => {
                    openCard(card, index);
                });
                card.addEventListener('keydown', (event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        openCard(card, index);
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

        // Update handlers if cards are dynamically removed
        const observer = new MutationObserver(() => {
            refreshCards();
            attachCardHandlers();
        });
        if (track) {
            observer.observe(track, { childList: true });
        }
    });
})();

(function () {
    const $ = (selector, scope = document) => scope.querySelector(selector);
    const $$ = (selector, scope = document) => Array.from(scope.querySelectorAll(selector));

    const escapeHtml = (value) => {
        const div = document.createElement('div');
        div.textContent = value;
        return div.innerHTML;
    };

    document.addEventListener('DOMContentLoaded', () => {
        const form = $('[data-contact-form]');
        if (!form) {
            return;
        }

        const botCheckbox = form.querySelector('[data-bot-check]');
        const submitButton = $('[data-form-submit]', form);
        const reviewModal = $('[data-review-modal]');
        const reviewCheckbox = reviewModal
            ? reviewModal.querySelector('[data-review-confirm]') || reviewModal.querySelector('input[name="review_confirmed"]')
            : null;
        const reviewError = reviewModal ? $('[data-review-error]', reviewModal) : null;
        const reviewStaticError = $('[data-review-error-static]', form);
        const closeButtons = reviewModal ? $$('[data-review-close]', reviewModal) : [];
        const editButton = reviewModal ? $('[data-review-edit]', reviewModal) : null;
        const sendButton = reviewModal ? $('[data-review-send]', reviewModal) : null;
        const backdrop = reviewModal ? reviewModal.querySelector('.modal__backdrop') : null;
        const requiredMessage = reviewModal ? reviewModal.dataset.errorRequired || '' : '';

        const updateSubmitState = () => {
            if (!submitButton) {
                return;
            }
            const isChecked = botCheckbox ? botCheckbox.checked : true;
            submitButton.disabled = !isChecked;
        };

        updateSubmitState();
        if (botCheckbox) {
            botCheckbox.addEventListener('change', updateSubmitState);
        }

        let allowSubmit = false;

        const hideStaticError = () => {
            if (reviewStaticError) {
                reviewStaticError.textContent = '';
                reviewStaticError.hidden = true;
            }
        };

        const showReviewError = (message) => {
            if (reviewError) {
                reviewError.textContent = message;
                reviewError.hidden = !message;
            }
        };

        const closeModal = () => {
            if (!reviewModal) {
                return;
            }
            reviewModal.classList.remove('is-visible');
            reviewModal.setAttribute('aria-hidden', 'true');
            document.body.classList.remove('has-modal');
            showReviewError('');
            if (reviewCheckbox) {
                reviewCheckbox.checked = false;
            }
        };

        const populateReview = () => {
            if (!reviewModal) {
                return;
            }
            const mapping = {
                first_name: 'first_name',
                last_name: 'last_name',
                phone: 'phone',
                email: 'email',
                company: 'company',
                message: 'message',
            };

            Object.entries(mapping).forEach(([fieldName, key]) => {
                const summaryField = reviewModal.querySelector(`[data-review-value="${key}"]`);
                if (!summaryField) {
                    return;
                }
                const element = form.elements.namedItem(fieldName);
                if (!element) {
                    summaryField.textContent = '';
                    return;
                }
                let value = '';
                if (element instanceof HTMLSelectElement) {
                    const option = element.options[element.selectedIndex];
                    value = option ? option.text : element.value;
                } else if (element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement) {
                    value = element.value;
                }

                if (key === 'message') {
                    summaryField.innerHTML = escapeHtml(value).replace(/\n/g, '<br>');
                } else {
                    summaryField.textContent = value;
                }
            });
        };

        const openModal = () => {
            if (!reviewModal) {
                return;
            }
            populateReview();
            hideStaticError();
            showReviewError('');
            if (reviewCheckbox) {
                reviewCheckbox.checked = false;
            }
            reviewModal.classList.add('is-visible');
            reviewModal.setAttribute('aria-hidden', 'false');
            document.body.classList.add('has-modal');
            const firstFocusable = reviewModal.querySelector('button, input, select, textarea');
            if (firstFocusable) {
                firstFocusable.focus();
            }
        };

        if (reviewCheckbox) {
            reviewCheckbox.addEventListener('change', () => {
                if (reviewCheckbox.checked) {
                    showReviewError('');
                }
            });
        }

        if (sendButton) {
            sendButton.addEventListener('click', () => {
                if (!reviewCheckbox || !reviewCheckbox.checked) {
                    showReviewError(requiredMessage);
                    return;
                }
                hideStaticError();
                allowSubmit = true;
                closeModal();
                if (typeof form.requestSubmit === 'function') {
                    form.requestSubmit();
                } else {
                    form.submit();
                }
            });
        }

        if (editButton) {
            editButton.addEventListener('click', () => {
                closeModal();
                const firstInput = form.querySelector('input, textarea, select');
                if (firstInput) {
                    firstInput.focus();
                }
            });
        }

        const closeButtonsCollection = closeButtons.concat(backdrop ? [backdrop] : []);
        closeButtonsCollection.forEach((element) => {
            if (!element) {
                return;
            }
            element.addEventListener('click', closeModal);
        });

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && reviewModal && reviewModal.classList.contains('is-visible')) {
                closeModal();
            }
        });

        form.addEventListener('submit', (event) => {
            if (allowSubmit) {
                allowSubmit = false;
                return;
            }
            event.preventDefault();
            const isChecked = botCheckbox ? botCheckbox.checked : true;
            if (!isChecked) {
                updateSubmitState();
                return;
            }
            openModal();
        });
    });
})();

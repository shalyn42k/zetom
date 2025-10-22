(function () {
    const ready = (callback) => {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', callback);
        } else {
            callback();
        }
    };

    ready(() => {
        const form = document.querySelector('[data-contact-form]');
        if (form) {
            const botCheckbox = form.querySelector('[data-bot-check]');
            const submitButton = form.querySelector('[data-form-submit]');
            const botError = form.querySelector('[data-bot-error]');
            const requiredMessage = form.dataset.botRequiredMessage || '';
            const reviewModal = form.querySelector('[data-review-modal]');
            const reviewFieldsContainer = reviewModal
                ? reviewModal.querySelector('[data-review-fields]')
                : null;
            const reviewOpenButton = form.querySelector('[data-review-open]');
            const reviewCloseElements = reviewModal
                ? reviewModal.querySelectorAll('[data-review-close]')
                : [];
            let restoreFocusTo = null;
            let reviewHideTimer = null;

            const getFieldLabel = (field) => {
                if (!field) {
                    return '';
                }
                const explicitLabel = field.getAttribute('data-review-label');
                if (explicitLabel) {
                    return explicitLabel;
                }
                if (field.id) {
                    const label = form.querySelector(`label[for="${field.id}"]`);
                    if (label) {
                        return label.textContent.replace(/\s+/g, ' ').trim();
                    }
                }
                const ariaLabel = field.getAttribute('aria-label');
                if (ariaLabel) {
                    return ariaLabel;
                }
                return field.name || '';
            };

            const createReviewInput = (field) => {
                const tagName = field.tagName.toLowerCase();
                let reviewInput;
                if (tagName === 'textarea') {
                    reviewInput = document.createElement('textarea');
                    reviewInput.rows = field.rows || 5;
                } else if (tagName === 'select') {
                    reviewInput = field.cloneNode(true);
                } else {
                    reviewInput = document.createElement('input');
                    reviewInput.type = field.type || 'text';
                }

                reviewInput.classList.add('form-input', 'review-field__input');
                reviewInput.name = '';
                reviewInput.id = '';
                reviewInput.dataset.reviewInput = field.dataset.reviewSource || field.name || '';
                const placeholder = field.getAttribute('placeholder');
                if (placeholder) {
                    reviewInput.setAttribute('placeholder', placeholder);
                }
                reviewInput.required = field.required;
                reviewInput.value = field.value;

                if (tagName === 'select') {
                    reviewInput.value = field.value;
                }

                const syncField = () => {
                    if (tagName === 'select') {
                        field.value = reviewInput.value;
                    } else {
                        field.value = reviewInput.value;
                    }
                    field.dispatchEvent(new Event('input', { bubbles: true }));
                    field.dispatchEvent(new Event('change', { bubbles: true }));
                };

                reviewInput.addEventListener('input', syncField);
                if (tagName === 'select') {
                    reviewInput.addEventListener('change', syncField);
                }

                return reviewInput;
            };

            const buildReviewFields = () => {
                if (!reviewFieldsContainer) {
                    return null;
                }
                reviewFieldsContainer.innerHTML = '';
                const reviewableFields = Array.from(
                    form.querySelectorAll('[data-review-source]')
                ).filter((field) => !field.closest('[data-review-modal]'));

                let firstInput = null;

                reviewableFields.forEach((field) => {
                    const labelText = getFieldLabel(field);
                    const wrapper = document.createElement('div');
                    wrapper.className = 'review-field';

                    if (labelText) {
                        const label = document.createElement('div');
                        label.className = 'review-field__label';
                        label.textContent = labelText;
                        wrapper.appendChild(label);
                    }

                    const reviewInput = createReviewInput(field);
                    wrapper.appendChild(reviewInput);
                    reviewFieldsContainer.appendChild(wrapper);

                    if (!firstInput) {
                        firstInput = reviewInput;
                    }
                });

                return firstInput;
            };

            const onReviewKeydown = (event) => {
                if (event.key === 'Escape' && reviewModal?.classList.contains('is-visible')) {
                    event.preventDefault();
                    closeReviewModal();
                }
            };

            const openReviewModal = () => {
                if (!reviewModal) {
                    return;
                }
                if (reviewHideTimer) {
                    clearTimeout(reviewHideTimer);
                    reviewHideTimer = null;
                }
                const firstInput = buildReviewFields();
                restoreFocusTo = document.activeElement instanceof HTMLElement ? document.activeElement : null;
                reviewModal.hidden = false;
                reviewModal.setAttribute('aria-hidden', 'false');
                requestAnimationFrame(() => {
                    reviewModal.classList.add('is-visible');
                });
                document.body.classList.add('has-open-modal');
                updateSubmitState();
                document.addEventListener('keydown', onReviewKeydown);

                if (firstInput instanceof HTMLElement) {
                    firstInput.focus({ preventScroll: true });
                }
            };

            const closeReviewModal = () => {
                if (!reviewModal) {
                    return;
                }
                reviewModal.classList.remove('is-visible');
                reviewModal.setAttribute('aria-hidden', 'true');
                document.body.classList.remove('has-open-modal');
                document.removeEventListener('keydown', onReviewKeydown);
                reviewHideTimer = window.setTimeout(() => {
                    reviewModal.hidden = true;
                    reviewHideTimer = null;
                }, 250);
                if (restoreFocusTo instanceof HTMLElement) {
                    restoreFocusTo.focus({ preventScroll: true });
                }
                restoreFocusTo = null;
            };

            if (reviewOpenButton && reviewModal) {
                reviewOpenButton.addEventListener('click', (event) => {
                    event.preventDefault();
                    if (typeof form.reportValidity === 'function' && !form.reportValidity()) {
                        return;
                    }
                    openReviewModal();
                });
            }

            reviewCloseElements.forEach((element) => {
                element.addEventListener('click', (event) => {
                    event.preventDefault();
                    closeReviewModal();
                });
            });

            const showBotError = (message) => {
                if (!botError) {
                    return;
                }
                botError.textContent = message;
                botError.hidden = !message;
            };

            const updateSubmitState = () => {
                if (!submitButton) {
                    return;
                }
                const isChecked = botCheckbox ? botCheckbox.checked : true;
                submitButton.disabled = !isChecked;
            };

            updateSubmitState();

            if (botCheckbox) {
                botCheckbox.addEventListener('change', () => {
                    updateSubmitState();
                    if (botCheckbox.checked) {
                        showBotError('');
                    }
                });
            }

            form.addEventListener('submit', (event) => {
                if (botCheckbox && !botCheckbox.checked) {
                    event.preventDefault();
                    updateSubmitState();
                    if (requiredMessage) {
                        showBotError(requiredMessage);
                        }
                    return;
                }

                if (submitButton) {
                    submitButton.disabled = true;
                }
                closeReviewModal();
            });
        }

        const successModal = document.querySelector('[data-success-modal]');
        if (successModal) {
            const closeElements = successModal.querySelectorAll('[data-success-close]');
            const closeModal = () => {
                successModal.classList.remove('is-visible');
                successModal.setAttribute('aria-hidden', 'true');
            };

            successModal.classList.add('is-visible');
            successModal.setAttribute('aria-hidden', 'false');

            closeElements.forEach((element) => {
                element.addEventListener('click', closeModal);
            });

            document.addEventListener('keydown', (event) => {
                if (event.key === 'Escape' && successModal.classList.contains('is-visible')) {
                    closeModal();
                }
            });
        }
    });
})();

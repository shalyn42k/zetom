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
        const reviewModal = document.querySelector('[data-review-modal]');
        if (form) {
            const botCheckbox = form.querySelector('[data-bot-check]');
            const submitButton = form.querySelector('[data-form-submit]');
            const botError = form.querySelector('[data-bot-error]');
            const requiredMessage = form.dataset.botRequiredMessage || '';
            const reviewSummaryValues = reviewModal ? reviewModal.querySelectorAll('[data-review-value]') : [];
            const reviewCloseElements = reviewModal ? reviewModal.querySelectorAll('[data-review-close]') : [];
            const reviewEditButtons = reviewModal ? reviewModal.querySelectorAll('[data-review-edit]') : [];
            const reviewSubmitButton = reviewModal ? reviewModal.querySelector('[data-review-submit]') : null;
            let hasConfirmedReview = false;

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

            const escapeHTML = (value) => value.replace(/[&<>"']/g, (char) => {
                switch (char) {
                    case '&':
                        return '&amp;';
                    case '<':
                        return '&lt;';
                    case '>':
                        return '&gt;';
                    case '"':
                        return '&quot;';
                    case '\'':
                        return '&#39;';
                    default:
                        return char;
                }
            });

            const formatValue = (value) => {
                if (!value) {
                    return '&mdash;';
                }
                return escapeHTML(value).replace(/\n/g, '<br>');
            };

            const updateReviewSummary = () => {
                if (!reviewModal) {
                    return;
                }
                reviewSummaryValues.forEach((element) => {
                    const fieldName = element.dataset.reviewValue;
                    if (!fieldName) {
                        return;
                    }
                    const field = form.elements.namedItem(fieldName);
                    if (!field) {
                        element.innerHTML = '&mdash;';
                        return;
                    }
                    const fieldValue = typeof field.value === 'string' ? field.value.trim() : '';
                    element.innerHTML = formatValue(fieldValue);
                });
            };

            const openReviewModal = () => {
                if (!reviewModal) {
                    return;
                }
                reviewModal.classList.add('is-visible');
                reviewModal.setAttribute('aria-hidden', 'false');
                document.body.classList.add('has-modal');
            };

            const closeReviewModal = () => {
                if (!reviewModal) {
                    return;
                }
                reviewModal.classList.remove('is-visible');
                reviewModal.setAttribute('aria-hidden', 'true');
                document.body.classList.remove('has-modal');
            };

            if (reviewModal) {
                reviewCloseElements.forEach((element) => {
                    element.addEventListener('click', () => {
                        closeReviewModal();
                        if (element.hasAttribute('data-review-back')) {
                            const firstEditable = form.querySelector('input:not([type="checkbox"]), textarea');
                            if (firstEditable) {
                                firstEditable.focus();
                            }
                        }
                    });
                });

                reviewEditButtons.forEach((button) => {
                    button.addEventListener('click', () => {
                        const fieldName = button.dataset.reviewEdit;
                        closeReviewModal();
                        if (fieldName) {
                            const field = form.elements.namedItem(fieldName);
                            if (field && typeof field.focus === 'function') {
                                field.focus();
                            }
                        }
                    });
                });

                document.addEventListener('keydown', (event) => {
                    if (event.key === 'Escape' && reviewModal.classList.contains('is-visible')) {
                        closeReviewModal();
                    }
                });

                if (reviewSubmitButton) {
                    reviewSubmitButton.addEventListener('click', () => {
                        hasConfirmedReview = true;
                        closeReviewModal();
                        if (typeof form.requestSubmit === 'function') {
                            form.requestSubmit();
                        } else {
                            form.submit();
                        }
                    });
                }
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

                if (reviewModal && !hasConfirmedReview) {
                    event.preventDefault();
                    updateReviewSummary();
                    openReviewModal();
                    return;
                }

                hasConfirmedReview = false;
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

function clearImageBorders() {
    window.location.href = "";
    const allImages = document.querySelectorAll('.popup-trigger img');
    allImages.forEach(image => {
        image.style.border = '2px solid transparent';
        image.style.borderRadius = '0';
        image.style.filter = 'sepia(0)';
    });
}
function highlightImage(imageName, imageId) {
    const allImages = document.querySelectorAll('.popup-trigger img');
    allImages.forEach(image => {
        image.style.border = '2px solid transparent';
        image.style.borderRadius = '0';
        image.style.filter = 'sepia(0)';
    });
    window.location.href = "#" + imageName;

    const image = document.getElementById(imageId);
    image.style.border = '2px solid lime';
    image.style.borderRadius = '5px';
    image.style.filter = 'sepia(1)';
}

$(document).ready(function () {
    $('details.assembly_details').each(function () {
        const summary = $(this).children('summary');
        const summaryText = summary.text();
        const span = $('<span>').text(summaryText);
        summary.text('').append(span);

        // Initially hide the summary text if the details element is open
        if (this.open) {
            span.hide();
        }

        $(this).on('toggle', function () {
            if (this.open) {
                span.hide();
            } else {
                span.show();
            }
        });
    });
});

class Accordion {
    constructor(el) {
        this.el = el;
        this.summary = el.querySelector('summary');
        this.content = el.querySelector('.detail_contents');

        this.animation = null;
        this.isClosing = false;
        this.isExpanding = false;
        this.summary.addEventListener('click', (e) => this.onClick(e));
    }

    onClick(e) {
        e.preventDefault();
        this.el.style.overflow = 'hidden';
        if (this.isClosing || !this.el.open) {
            this.open();
        } else if (this.isExpanding || this.el.open) {
            this.shrink();
        }
    }

    shrink() {
        this.isClosing = true;

        const startHeight = `${this.el.offsetHeight}px`;
        const endHeight = `${this.summary.offsetHeight + 15}px`;

        if (this.animation) {
            this.animation.cancel();
        }

        this.animation = this.el.animate({
            height: [startHeight, endHeight]
        }, {
            duration: 400,
            easing: 'ease-out'
        });

        this.animation.onfinish = () => this.onAnimationFinish(false);
        this.animation.oncancel = () => this.isClosing = false;
    }

    open() {
        this.el.style.height = `${this.el.offsetHeight + 10}px`;
        this.el.open = true;
        window.requestAnimationFrame(() => this.expand());
    }

    expand() {
        this.isExpanding = true;
        const startHeight = `${this.el.offsetHeight}px`;
        const endHeight = `${this.summary.offsetHeight + this.content.offsetHeight + 10}px`;

        if (this.animation) {
            this.animation.cancel();
        }

        this.animation = this.el.animate({
            height: [startHeight, endHeight]
        }, {
            duration: 400,
            easing: 'ease-out'
        });
        this.animation.onfinish = () => this.onAnimationFinish(true);
        this.animation.oncancel = () => this.isExpanding = false;
    }

    onAnimationFinish(open) {
        this.el.open = open;
        this.animation = null;
        this.isClosing = false;
        this.isExpanding = false;
        this.el.style.height = this.el.style.overflow = '';
    }
}

document.querySelectorAll('details').forEach((el) => {
    new Accordion(el);
});
/* ============================================
   Landing Page Animations
   ============================================ */

// Intersection Observer for scroll-triggered animations
const observerOptions = {
  threshold: 0.15,
  rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add('animate-in');
      observer.unobserve(entry.target);
    }
  });
}, observerOptions);

// Observe elements for scroll animations
document.addEventListener('DOMContentLoaded', () => {
  // Observe all sections and cards
  const elementsToObserve = document.querySelectorAll(
    '.hero, .topics-section, .topic-card, .section-title, .section-subtitle'
  );

  elementsToObserve.forEach(el => {
    observer.observe(el);
  });

  animateStats();
  addPageLoadAnimation();
});

// Animate stats counter
function animateStats() {
  const statsItems = document.querySelectorAll('.stat-item');

  statsItems.forEach((item) => {
    const statNumber = item.querySelector('.stat-number');
    if (!statNumber) return;

    const text = statNumber.textContent.trim();
    const numberMatch = text.match(/(\d+)/);
    if (!numberMatch) return;

    const targetNumber = parseInt(numberMatch[1]);
    const fullText = text;

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const startTime = Date.now();
          const duration = 1200; // milliseconds

          const interval = setInterval(() => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Easing function
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const currentNumber = Math.floor(targetNumber * easeOut);

            statNumber.textContent = currentNumber + '+';

            if (progress === 1) {
              clearInterval(interval);
              statNumber.textContent = fullText;
              observer.unobserve(item);
            }
          }, 30);
        }
      });
    }, { threshold: 0.3 });

    observer.observe(item);
  });
}

// Add fade-in animation to page on load
function addPageLoadAnimation() {
  const header = document.querySelector('.header');
  const heroSection = document.querySelector('.hero');

  if (header) {
    header.style.animation = 'fadeIn 0.6s ease-out';
  }

  if (heroSection) {
    heroSection.style.opacity = '1';
  }
}

// Smooth scroll behavior for anchor links
document.addEventListener('click', (e) => {
  if (e.target.closest('a')) {
    const link = e.target.closest('a');
    const href = link.getAttribute('href');

    if (href && href.startsWith('#')) {
      const targetId = href.substring(1);
      const targetElement = document.getElementById(targetId);

      if (targetElement) {
        e.preventDefault();
        targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  }
});

// Add hover scale effect to images
document.addEventListener('DOMContentLoaded', () => {
  const images = document.querySelectorAll('img');
  images.forEach((img) => {
    img.addEventListener('mouseenter', () => {
      img.style.transform = 'scale(1.05)';
    });
    img.addEventListener('mouseleave', () => {
      img.style.transform = 'scale(1)';
    });
  });
});

// Button ripple effect
function createRipple(event) {
  const button = event.currentTarget;
  const circle = document.createElement('span');
  const diameter = Math.max(button.clientWidth, button.clientHeight);
  const radius = diameter / 2;

  circle.style.width = circle.style.height = diameter + 'px';
  circle.style.left = event.clientX - button.offsetLeft - radius + 'px';
  circle.style.top = event.clientY - button.offsetTop - radius + 'px';
  circle.classList.add('ripple');

  const ripple = button.querySelector('.ripple');
  if (ripple) ripple.remove();

  button.appendChild(circle);
}

// Add ripple effect to buttons
document.querySelectorAll('.btn-cta, .btn-login, .topic-link').forEach((button) => {
  button.addEventListener('click', createRipple);
});

// Smooth fade-in for topic cards on view
document.addEventListener('DOMContentLoaded', () => {
  const topicCards = document.querySelectorAll('.topic-card');

  const cardObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry, index) => {
        if (entry.isIntersecting) {
          entry.target.style.animation = `slideUp 0.6s ease-out ${index * 0.15}s both`;
          cardObserver.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1 }
  );

  topicCards.forEach((card) => {
    cardObserver.observe(card);
  });
});

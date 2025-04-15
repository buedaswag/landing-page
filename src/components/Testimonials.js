function Testimonials() {
  return (
    <section data-testid="testimonial-section" className="testimonials">
      <h2 className="section-title">What Clients Say</h2>
      
      <div className="testimonials-container">
        {/* Row 1 */}
        <div className="testimonial-row">
          {/* Moved Jukka's testimonial to the left */}
          <div className="testimonial-card">
            <blockquote>
              "Miguel organized everything for us, we just had to join the workshops and get immediate value from them. We invested a bit, but the outcome is huge. Even if no further actions are taken, simply doing the workshops shows you what the bottlenecks are, what's slowing you down, and what is hurting the processes."
            </blockquote>
            <div className="testimonial-author">
              <h3>Jukka Palosaari</h3>
              <p>Director of Engineering, Relex Solutions</p>
            </div>
            <a href="#" className="testimonial-link">Read Full Testimonial →</a>
          </div>
          
          {/* Iker's testimonial - unchanged position */}
          <div className="testimonial-card">
            <blockquote>
              "All the workshops led us to the outcome we were expecting and got a good overview on areas we could improve to make the whole process more efficient. It was great to see the whole process, Miguel's facilitation skills as well as his VSM expertise."
            </blockquote>
            <div className="testimonial-author">
              <h3>Iker Garagarza</h3>
              <p>Director of Engineering, Relex Solutions</p>
            </div>
            <a href="#" className="testimonial-link">Read Full Testimonial →</a>
          </div>
        </div>
        
        {/* Row 2 */}
        <div className="testimonial-row">
          {/* Mark's testimonial - new, below Iker's */}
          <div className="testimonial-card">
            <blockquote>
              "Miguel has a strong background and fantastic knowledge of DevOps, Data Engineering and Analytics. He used this effectively in bringing teams together and conducting Value Stream mapping and helping to identify how we could reduce process cycle times and implement process improvement. Miguel was always very professional, friendly and a great team player."
            </blockquote>
            <div className="testimonial-author">
              <h3>Mark Sadler</h3>
              <p>Program Director, Relex Solutions</p>
            </div>
            <a href="#" className="testimonial-link">Read Full Testimonial →</a>
          </div>
          
          {/* Mika's testimonial - unchanged position */}
          <div className="testimonial-card">
            <blockquote>
              "The value stream mapping Miguel organized for our Identity Service team had several impacts. On one side, a tremendous potential was unveiled how the process of deploying changes can be improved. On the other, it was a great team building exercise."
            </blockquote>
            <div className="testimonial-author">
              <h3>Mika Schafroth</h3>
              <p>Director of Engineering, Relex Solutions</p>
            </div>
            <a href="#" className="testimonial-link">Read Full Testimonial →</a>
          </div>
        </div>
      </div>
    </section>
  );
}

export default Testimonials; 
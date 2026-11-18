import styled from "@emotion/styled";

const Frame = styled.object`
  display: block;
  pointer-events: none;
`;

/**
 * An animated SVG that starts somewhere random in its loop. An <img> always starts at the
 * beginning, but an <object> can reach into the SVG's own clock.
 */
const RandomStartSvg = ({ src, loopSeconds }: { src: string; loopSeconds: number }) => (
  <Frame
    data={src}
    type="image/svg+xml"
    aria-hidden
    tabIndex={-1}
    onLoad={(e) => {
      const svg = e.currentTarget.contentDocument?.querySelector("svg");
      if (!svg) return;
      // Its own width and height would otherwise fix its size inside the frame.
      svg.setAttribute("width", "100%");
      svg.setAttribute("height", "100%");
      svg.setCurrentTime(Math.random() * loopSeconds);
    }}
  />
);

export default RandomStartSvg;

import React, { useState } from "react";
import { Popover as TinyPopover } from "react-tiny-popover";

/**
 * A component that represents a button and a box that appears when the button is clicked/hovered over.
 */
const Popover = ({ hover, button, style, children }) => {
  const [isShown, setIsShown] = useState(false);
  const onToggle = (val) => {
    setIsShown(!val ? !isShown : val);
  };
  return (
    <TinyPopover
      isOpen={isShown}
      positions={["left", "bottom", "right", "up"]}
      content={
        <div
          className="msg"
          style={{
            ...style,
          }}
        >
          {children}
        </div>
      }
    >
      <span
        style={{ cursor: "pointer" }}
        onClick={!hover ? () => onToggle() : undefined}
        onMouseEnter={hover ? () => onToggle(true) : undefined}
        onMouseLeave={hover ? () => onToggle(false) : undefined}
      >
        {button || <button type="button">Toggle</button>}
      </span>
    </TinyPopover>
  );
};

const PopoverTitle = ({ children, title }) => (
  <Popover hover button={children}>
    {title}
  </Popover>
);

export { PopoverTitle, Popover };

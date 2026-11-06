import React, { useState, useEffect, useRef } from "react";
import styled from "@emotion/styled";
import { DBObject } from "../../types";
import { PanelHeaderSkeleton } from "./PanelCommon";

const Wrapper = styled.div`
  position: relative;
  display: flex;
  flex: 1 1 auto;
  min-width: 0;
`;

const Trigger = styled.button<{ $isOpen: boolean }>`
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 0;
  max-width: 100%;
  padding: 0.35rem 0.5rem;
  margin-left: -0.5rem;
  border: none;
  border-radius: 5px;
  background: ${(props) =>
    props.$isOpen ? "rgba(61, 65, 119, 0.08)" : "transparent"};
  color: var(--primary-color-ultra-dark);
  font-family: inherit;
  font-size: 1.25rem;
  font-weight: 700;
  cursor: pointer;

  &:hover {
    background: rgba(61, 65, 119, 0.08);
  }

  i {
    font-size: 0.7rem;
    transition: transform 200ms ease;
  }

  &[aria-expanded="true"] i {
    transform: rotate(180deg);
  }

  @media (prefers-reduced-motion: reduce) {
    i {
      transition: none;
    }
  }
`;

const TriggerName = styled.span`
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
`;

const Menu = styled.div<{ $open: boolean }>`
  position: absolute;
  top: calc(100% + 0.35rem);
  left: -0.5rem;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 16rem;
  max-width: min(24rem, calc(100vw - 2rem));
  padding: 0.35rem;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12), 0 0 0 1px rgba(61, 65, 119, 0.06);
  transform-origin: top left;
  opacity: ${(props) => (props.$open ? 1 : 0)};
  transform: ${(props) =>
    props.$open ? "none" : "translateY(-4px) scale(0.98)"};
  visibility: ${(props) => (props.$open ? "visible" : "hidden")};
  transition: opacity 150ms ease, transform 150ms ease,
    visibility 0s linear ${(props) => (props.$open ? "0s" : "150ms")};

  @media (prefers-reduced-motion: reduce) {
    transition: none;
  }
`;

const Item = styled.div<{ $isActive: boolean }>`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.55rem 0.5rem 0.55rem 0.75rem;
  border-radius: 6px;
  background: ${(props) =>
    props.$isActive ? "var(--primary-color-light)" : "transparent"};
  color: var(--primary-color-ultra-dark);
  font-size: 1rem;
  font-weight: ${(props) => (props.$isActive ? 700 : 500)};
  cursor: pointer;

  &:hover {
    background: var(--primary-color-light);
  }

  &:hover .item-actions,
  &:focus-within .item-actions {
    opacity: 1;
  }
`;

const ItemName = styled.span`
  flex: 1;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
`;

const Actions = styled.span`
  display: flex;
  flex-shrink: 0;
  gap: 0.1rem;
  opacity: 0;
  transition: opacity 0.1s ease;
`;

const ActionButton = styled.button`
  display: grid;
  place-items: center;
  width: 1.75rem;
  height: 1.75rem;
  padding: 0;
  border: none;
  border-radius: 5px;
  background: none;
  color: var(--primary-color-xxx-dark);
  font-size: 0.85rem;
  cursor: pointer;

  &:hover {
    background: rgba(61, 65, 119, 0.1);
    color: var(--primary-color-ultra-dark);
  }

  &.danger:hover {
    color: var(--error-color);
  }
`;

const Divider = styled.div`
  height: 1px;
  margin: 0.15rem 0.35rem;
  background: rgba(129, 154, 225, 0.35);
`;

const AddNew = styled.button`
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.55rem 0.75rem;
  border: none;
  border-radius: 6px;
  background: none;
  color: var(--primary-color-xxx-dark);
  font-family: inherit;
  font-size: 1rem;
  font-weight: 500;
  text-align: left;
  cursor: pointer;

  &:hover:not(:disabled) {
    background: var(--primary-color-light);
  }

  &:disabled {
    opacity: 0.6;
    cursor: default;
  }

  i {
    font-size: 0.85rem;
  }
`;

interface SelectListDropdownProps<T extends DBObject> {
  itemType: string; // e.g., Degree Plan or Degree
  active?: T;
  allItems: T[];
  selectItem: (id: T["id"]) => void;
  getItemName: (item: T) => string;
  mutators: {
    copy?: (item: T) => void;
    remove?: (item: T) => void;
    rename?: (item: T) => void;
    create: () => void;
  };
  isLoading: boolean;
}

const SelectListDropdown = <T extends DBObject>({
  itemType,
  active,
  allItems,
  selectItem,
  getItemName,
  mutators: { copy, remove, rename, create },
  isLoading,
}: SelectListDropdownProps<T>) => {
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return undefined;
    const close = (event: MouseEvent) => {
      if (!ref.current?.contains(event.target as Node)) setIsOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [isOpen]);

  if (!active) return <PanelHeaderSkeleton />;

  const action = (run: () => void) => (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsOpen(false);
    run();
  };

  return (
    <Wrapper ref={ref}>
      <Trigger
        type="button"
        $isOpen={isOpen}
        aria-haspopup="menu"
        aria-expanded={isOpen}
        onClick={() => setIsOpen(!isOpen)}
      >
        <TriggerName>{getItemName(active)}</TriggerName>
        <i className="fas fa-chevron-down" aria-hidden />
      </Trigger>
      <Menu role="menu" $open={isOpen}>
        {allItems.map((item) => {
          const name = getItemName(item);
          return (
            <Item
              key={String(item.id)}
              role="menuitemradio"
              aria-checked={item.id === active.id}
              tabIndex={0}
              $isActive={item.id === active.id}
              onClick={() => {
                selectItem(item.id);
                setIsOpen(false);
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  selectItem(item.id);
                  setIsOpen(false);
                }
              }}
            >
              <ItemName title={name}>{name}</ItemName>
              <Actions className="item-actions">
                {rename && (
                  <ActionButton
                    type="button"
                    aria-label={`Rename ${name}`}
                    title="Rename"
                    onClick={action(() => rename(item))}
                  >
                    <i className="far fa-edit" aria-hidden />
                  </ActionButton>
                )}
                {copy && (
                  <ActionButton
                    type="button"
                    aria-label={`Copy ${name}`}
                    title="Copy"
                    onClick={action(() => copy(item))}
                  >
                    <i className="far fa-copy" aria-hidden />
                  </ActionButton>
                )}
                {remove && (
                  <ActionButton
                    type="button"
                    className="danger"
                    aria-label={`Delete ${name}`}
                    title="Delete"
                    onClick={action(() => remove(item))}
                  >
                    <i className="fas fa-trash" aria-hidden />
                  </ActionButton>
                )}
              </Actions>
            </Item>
          );
        })}
        <Divider />
        <AddNew
          type="button"
          role="menuitem"
          disabled={isLoading}
          onClick={() => {
            setIsOpen(false);
            create();
          }}
        >
          <i className="fas fa-plus" aria-hidden />
          Add new {itemType}
        </AddNew>
      </Menu>
    </Wrapper>
  );
};

export default SelectListDropdown;

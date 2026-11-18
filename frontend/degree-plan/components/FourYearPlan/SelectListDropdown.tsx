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

export const Menu = styled.div<{ $open: boolean; $wide?: boolean }>`
  position: absolute;
  top: calc(100% + 0.35rem);
  left: -0.5rem;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  /* Previews take a row's right end, so names keep about 6rem beside four of them. */
  min-width: ${(props) => (props.$wide ? "min(24rem, calc(100vw - 2rem))" : "16rem")};
  max-width: min(${(props) => (props.$wide ? "28rem" : "24rem")}, calc(100vw - 2rem));
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

// Scrolls on its own so a long list doesn't run off the page, keeping "Add new" in view.
const ItemList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  max-height: min(28rem, calc(100vh - 12rem));
  max-height: min(28rem, calc(100dvh - 12rem));
  overflow-y: auto;
  overscroll-behavior: contain;
`;

// Room for an item's three actions (1.75rem each), which take the right end of a hovered row.
const ACTIONS_WIDTH = "6rem";

export const Item = styled.div<{ $isActive: boolean }>`
  position: relative;
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
    pointer-events: auto;
  }

  &:hover .item-preview,
  &:focus-within .item-preview {
    transform: translateX(-${ACTIONS_WIDTH});
    --preview-open: 1; /* for a preview's own parts to move with it */
  }
`;

// Leaves a gap the width of the actions, which the preview slides into when they show.
const NARROW = "(max-width: 30rem)";

const Preview = styled.span`
  display: flex;
  flex-shrink: 0;
  margin-left: auto;
  padding-left: calc(${ACTIONS_WIDTH} + 0.5rem);
  transition: transform 0.2s ease;

  @media (prefers-reduced-motion: reduce) {
    transition: none;
  }
  @media ${NARROW} {
    display: none;
  }
`;

const ItemName = styled.span`
  flex: 1;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
`;

// Shows at the right end of a hovered row, where its preview was.
const Actions = styled.span`
  position: absolute;
  top: 50%;
  right: 0.5rem;
  transform: translateY(-50%);
  display: flex;
  gap: 0.1rem;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease;

  @media ${NARROW} {
    position: static;
    transform: none;
    flex-shrink: 0;
  }
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

  &:disabled {
    opacity: 0.4;
    cursor: default;
    background: none;
  }
`;

const LimitNote = styled.div`
  padding: 0 0.75rem 0.35rem;
  font-size: 0.8rem;
  color: var(--primary-color-extra-dark);
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
  maxItems?: number; // at the limit, nothing more can be added or copied
  preview?: (item: T) => React.ReactNode; // shown beside each item's name
  onOpen?: () => void;
}

const SelectListDropdown = <T extends DBObject>({
  itemType,
  active,
  allItems,
  selectItem,
  getItemName,
  mutators: { copy, remove, rename, create },
  isLoading,
  maxItems,
  preview,
  onOpen,
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

  const atLimit = maxItems !== undefined && allItems.length >= maxItems;

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
        onClick={() => {
          if (!isOpen) onOpen?.();
          setIsOpen(!isOpen);
        }}
      >
        <TriggerName>{getItemName(active)}</TriggerName>
        <i className="fas fa-chevron-down" aria-hidden />
      </Trigger>
      <Menu role="menu" $open={isOpen} $wide={!!preview}>
        <ItemList>
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
                  // Keys pressed on the row's own buttons are theirs.
                  if (e.target !== e.currentTarget) return;
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    selectItem(item.id);
                    setIsOpen(false);
                  }
                }}
              >
                <ItemName title={name}>{name}</ItemName>
                {preview && <Preview className="item-preview">{preview(item)}</Preview>}
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
                      title={
                        atLimit ? `You can have up to ${maxItems}` : "Copy"
                      }
                      disabled={atLimit}
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
        </ItemList>
        <Divider />
        <AddNew
          type="button"
          role="menuitem"
          disabled={isLoading || atLimit}
          onClick={() => {
            setIsOpen(false);
            create();
          }}
        >
          <i className="fas fa-plus" aria-hidden />
          Add new {itemType}
        </AddNew>
        {atLimit && (
          <LimitNote>
            You can have up to {maxItems} {itemType}s. Delete one to add
            another.
          </LimitNote>
        )}
      </Menu>
    </Wrapper>
  );
};

export default SelectListDropdown;

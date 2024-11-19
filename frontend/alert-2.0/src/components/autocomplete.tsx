import { Command as CommandPrimitive } from 'cmdk'
import React, { useState } from 'react'

import {
	Command,
	CommandEmpty,
	CommandGroup,
	CommandItem,
	CommandList,
} from './ui/command'
import { Input } from './ui/input'
import { Popover, PopoverAnchor, PopoverContent } from './ui/popover'
import { Skeleton } from './ui/skeleton'

export interface ItemEntry<T> {
	id: string
	value: T
}

interface Props<T> {
	searchValue?: string
	onSearchValueChange?: (value: string) => void
	onSelect?: (obj: ItemEntry<T>) => void

	items: ItemEntry<T>[]
	isLoading?: boolean

	emptyMessage?: string
	placeholder?: string

	ItemComponent: React.FC<{ item: ItemEntry<T> }>
}

export function AutoComplete<T>({
	searchValue,
	onSearchValueChange,
	onSelect,

	items,
	isLoading,

	emptyMessage,
	placeholder,

	ItemComponent,
}: Props<T>) {
	const [open, setOpen] = useState(false)

	const reset = () => {
		onSearchValueChange?.('')
	}

	const onInputBlur = (e: React.FocusEvent<HTMLInputElement>) => {
		if (!e.relatedTarget?.hasAttribute('cmdk-list')) {
			reset()
		}
	}

	const onSelectItem = (entry: ItemEntry<T>) => {
		onSelect?.(entry)
		setOpen(false)
	}

	return (
		<div className="flex items-center">
			<Popover open={open} onOpenChange={setOpen}>
				<Command shouldFilter={false}>
					<PopoverAnchor asChild>
						<CommandPrimitive.Input
							asChild
							value={searchValue}
							onValueChange={onSearchValueChange}
							onKeyDown={e => setOpen(e.key !== 'Escape')}
							onMouseDown={() => setOpen(open => !!searchValue || !open)}
							onFocus={() => setOpen(true)}
							onBlur={onInputBlur}
						>
							<Input placeholder={placeholder} />
						</CommandPrimitive.Input>
					</PopoverAnchor>
					{!open && <CommandList aria-hidden="true" className="hidden" />}
					<PopoverContent
						asChild
						onOpenAutoFocus={e => e.preventDefault()}
						onInteractOutside={e => {
							if (
								e.target instanceof Element &&
								e.target.hasAttribute('cmdk-input')
							) {
								e.preventDefault()
							}
						}}
						className="w-[--radix-popover-trigger-width] p-0"
					>
						<CommandList>
							{isLoading && (
								<CommandPrimitive.Loading>
									<div className="p-1">
										<Skeleton className="h-6 w-full" />
									</div>
								</CommandPrimitive.Loading>
							)}
							{items.length > 0 && !isLoading ? (
								<CommandGroup>
									{items.map(item => (
										<CommandItem
											key={item.id}
											value={item.id}
											onMouseDown={e => e.preventDefault()}
											onSelect={() => onSelectItem(item)}
										>
											<ItemComponent item={item} />
										</CommandItem>
									))}
								</CommandGroup>
							) : null}
							{!isLoading ? (
								<CommandEmpty>{emptyMessage ?? 'No items.'}</CommandEmpty>
							) : null}
						</CommandList>
					</PopoverContent>
				</Command>
			</Popover>
		</div>
	)
}

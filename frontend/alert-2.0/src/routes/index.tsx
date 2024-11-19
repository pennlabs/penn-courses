import { zodResolver } from '@hookform/resolvers/zod'
import { createFileRoute } from '@tanstack/react-router'
import { useForm } from 'react-hook-form'
import { useAuth } from 'react-oidc-context'
import { toast } from 'sonner'
import { z } from 'zod'

import { CourseSectionContent } from '@/components/CourseSection'
import { CourseSectionAutocomplete } from '@/components/CourseSectionAutocomplete'
import { PCAHeader } from '@/components/PCAHeader'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import {
	Form,
	FormControl,
	FormField,
	FormItem,
	FormLabel,
	FormMessage,
} from '@/components/ui/form'
import { trpc } from '@/core/trpc'
import { CourseSection } from '@/core/types'
import { cn } from '@/lib/utils'

const formSchema = z.object({
	sections: z
		.array(z.custom<CourseSection>())
		.nonempty('You must select at least 1 course (section)'),
})

type FormValues = z.infer<typeof formSchema>

const AlertForm: React.FC = () => {
	const auth = useAuth()
	const email = auth.user?.profile.email

	const { mutateAsync: register } = trpc.alert.register.useMutation()

	const form = useForm<FormValues>({
		resolver: zodResolver(formSchema),
		defaultValues: {
			sections: [],
		},
	})

	const handleSubmit = form.handleSubmit(async ({ sections }) => {
		const fullSectionCodes = sections.map(section => section.section_id)
		try {
			const result = await register({ sectionCodes: fullSectionCodes })
			if (result.insertedSections.length > 0) {
				toast.success(
					`Successfully registered alerts for ${result.insertedSections.join(', ')}`,
				)
			}
			if (result.duplicateSections.length > 0) {
				toast.error(
					`Already registered alerts for ${result.duplicateSections.join(', ')}`,
				)
			}
		} catch (error) {
			toast.error('Failed to register for alerts')
		}
	})

	return (
		<Form {...form}>
			<form onSubmit={handleSubmit}>
				<FormField
					control={form.control}
					name="sections"
					render={({ field }) => (
						<FormItem>
							<FormLabel>Course</FormLabel>
							<FormControl>
								<div>
									<CourseSectionAutocomplete
										onCourseSectionSelected={section =>
											void (
												!field.value.find(
													s => s.section_id === section.section_id,
												) && field.onChange([...field.value, section])
											)
										}
									/>
									<div>
										{field.value.map(section => (
											<Card
												key={section.section_id}
												className={cn('shadow-none', 'mt-4')}
											>
												<CardContent
													className={cn(
														'p-2',
														'flex',
														'items-center',
														'space-x-4',
													)}
												>
													<CourseSectionContent
														section={section}
														className={cn('w-full')}
													/>
													<div
														role="button"
														className={cn('bg-red-100', 'rounded-full', 'p-2')}
														onClick={() =>
															field.onChange(
																field.value.filter(
																	s => s.section_id !== section.section_id,
																),
															)
														}
													>
														<div
															style={{
																mask: 'url(/assets/icons/x.svg) no-repeat center',
															}}
															className={cn('w-2', 'h-2', 'bg-red-600')}
														/>
													</div>
												</CardContent>
											</Card>
										))}
									</div>
								</div>
							</FormControl>
							<FormMessage />
						</FormItem>
					)}
				/>

				<div className={cn('text-sm', 'text-gray-700', 'mt-4')}>
					We'll send an email to{' '}
					<span className={cn('font-bold')}>{email}</span> to let you know when
					a course section you've selected has an open seat.
				</div>

				<Button
					disabled={!form.formState.isValid || form.formState.isSubmitting}
					type="submit"
					className={cn('w-full', 'mt-4')}
				>
					{form.formState.isSubmitting
						? 'Submitting...'
						: 'Register for Alerts'}
				</Button>
			</form>
		</Form>
	)
}

const Page: React.FC = () => {
	return (
		<main className={cn('flex', 'flex-col', 'items-center', 'justify-between')}>
			<Card className={cn('w-[calc(100vw-20px)]', 'max-w-[480px]')}>
				<CardHeader>
					<PCAHeader />
				</CardHeader>
				<CardContent>
					<AlertForm />
				</CardContent>
			</Card>
			<div className={cn('mt-4', 'text-sm', 'text-gray-500')}>
				Made with ❤️ by{' '}
				<a
					href="https://pennlabs.org"
					target="_blank"
					className={cn('text-blue-500')}
				>
					Penn Labs
				</a>
			</div>
		</main>
	)
}

export const Route = createFileRoute('/')({
	component: Page,
})

def recompute_historical_probabilities(current_semester, verbose=False):
    """
    Recomputes the historical probabilities for all topics.
    """
    if verbose:
        print("Recomputing historical probabilities for all topics...")
    topics = Topic.objects.all()
    # Iterate over each Topic
    for topic in topics:
        # Calculate historical_year_probability for the current topic
        test = topic.courses.order_by("semester").all()
        historical_prob = historical_year_probability(current_semester, test)
        # Update the historical_probabilities field for the current topic
        topic.historical_probabilities_spring = historical_prob[0]
        topic.historical_probabilities_summer = historical_prob[1]
        topic.historical_probabilities_fall = historical_prob[0]
        topic.save()
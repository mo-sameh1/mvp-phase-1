export function LoadingState({ message = "Loading..." }: { message?: string }) {
  return (
    <section className="state-block" aria-live="polite">
      <div className="loading-dot" aria-hidden="true" />
      <p>{message}</p>
    </section>
  );
}

export function ErrorState({ title = "Something went wrong", message }: StateProps) {
  return (
    <section className="state-block error" role="alert">
      <h2>{title}</h2>
      <p>{message}</p>
    </section>
  );
}

export function EmptyState({ title, message }: StateProps) {
  return (
    <section className="state-block">
      <h2>{title}</h2>
      <p>{message}</p>
    </section>
  );
}

type StateProps = {
  title: string;
  message: string;
};
